#!/bin/bash
#
# Update YOLO LAB Popular Posts Configuration
#
# Automatically fetches latest popular posts data and optionally commits to git
# Designed to run on a schedule (e.g., weekly via cron or Task Scheduler)
#
# Usage:
#   ./scripts/update-popular-posts.sh                 # Run update
#   ./scripts/update-popular-posts.sh --no-commit     # Don't commit to git
#   ./scripts/update-popular-posts.sh --test          # Test mode (dry-run)
#
# Installation (Linux/macOS):
#   crontab -e
#   # Add: 0 2 * * 1 cd /path/to/project && ./scripts/update-popular-posts.sh
#

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="${PROJECT_DIR}/scripts/fetch-popular-posts.js"
CONFIG_FILE="${PROJECT_DIR}/data/popular-posts.json"
LOG_FILE="${PROJECT_DIR}/logs/popular-posts-update.log"
DEPLOY_SCRIPT="${PROJECT_DIR}/scripts/deploy-yolo-homepage.js"

# Options
DO_COMMIT=true
TEST_MODE=false
DEPLOY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-commit)
      DO_COMMIT=false
      shift
      ;;
    --test)
      TEST_MODE=true
      shift
      ;;
    --deploy)
      DEPLOY=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create logs directory if needed
mkdir -p "${PROJECT_DIR}/logs"

# Log function
log() {
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[${timestamp}] $1" | tee -a "${LOG_FILE}"
}

log "════════════════════════════════════════════════════════════════"
log "YOLO LAB Popular Posts Update Script"
log "════════════════════════════════════════════════════════════════"

# Verify script exists
if [[ ! -f "${SCRIPT_PATH}" ]]; then
  log "✗ Error: Script not found at ${SCRIPT_PATH}"
  exit 1
fi

log "✓ Found fetch script: ${SCRIPT_PATH}"
log "✓ Config file: ${CONFIG_FILE}"

# Run fetch script
log ""
log "📡 Fetching latest popular posts data..."
log "─────────────────────────────────────────────────────────────────"

if node "${SCRIPT_PATH}"; then
  log "✓ Popular posts data fetched successfully"
else
  log "✗ Failed to fetch popular posts data"
  exit 1
fi

# Verify config was generated
if [[ ! -f "${CONFIG_FILE}" ]]; then
  log "✗ Error: Config file not generated at ${CONFIG_FILE}"
  exit 1
fi

log ""
log "✓ Config file verified: ${CONFIG_FILE}"
log "─────────────────────────────────────────────────────────────────"

# Show summary
log ""
log "📋 Update Summary:"

# Extract key info from config
if command -v jq &> /dev/null; then
  ARTICLE_COUNT=$(jq '.include_ids | length' "${CONFIG_FILE}")
  SOURCE=$(jq -r '.meta.source' "${CONFIG_FILE}")
  GENERATED_AT=$(jq -r '.generated_at' "${CONFIG_FILE}")

  log "  Source: ${SOURCE}"
  log "  Articles: ${ARTICLE_COUNT}"
  log "  Generated: ${GENERATED_AT}"
  log "  IDs: $(jq -r '.include_ids | join(", ")' "${CONFIG_FILE}")"
else
  log "  (jq not available for detailed summary)"
fi

# Optional: Commit to git
if [[ "${DO_COMMIT}" == true ]]; then
  log ""
  log "📝 Git Operations:"
  log "─────────────────────────────────────────────────────────────────"

  cd "${PROJECT_DIR}"

  # Check if git repo exists
  if git rev-parse --git-dir > /dev/null 2>&1; then
    # Check if there are changes
    if git diff --quiet "${CONFIG_FILE}" 2>/dev/null || [[ $(git diff --cached --quiet "${CONFIG_FILE}" 2>/dev/null; echo $?) != 0 ]]; then
      log "✓ Git repository detected"

      # Stage changes
      git add "${CONFIG_FILE}"
      log "✓ Staged: ${CONFIG_FILE}"

      # Create commit
      COMMIT_MSG="chore: update popular posts configuration"
      git commit -m "${COMMIT_MSG}"
      log "✓ Committed: ${COMMIT_MSG}"
    else
      log "ℹ No changes to commit"
    fi
  else
    log "⚠ Not a git repository. Skipping commit."
  fi
fi

# Optional: Deploy to production
if [[ "${DEPLOY}" == true ]]; then
  log ""
  log "🚀 Deploying to Production:"
  log "─────────────────────────────────────────────────────────────────"

  if [[ ! -f "${DEPLOY_SCRIPT}" ]]; then
    log "✗ Error: Deploy script not found at ${DEPLOY_SCRIPT}"
    exit 1
  fi

  if node "${DEPLOY_SCRIPT}"; then
    log "✓ Deployment completed successfully"
  else
    log "✗ Deployment failed"
    exit 1
  fi
fi

log ""
log "════════════════════════════════════════════════════════════════"
log "✓ Update completed successfully"
log "════════════════════════════════════════════════════════════════"
log ""
