#!/bin/bash
# frontmatter-backfill.sh — Automatic frontmatter field completion
# Fills missing required fields (domain, maturity, updated, created, tags)
# for notes that were created without full metadata.
#
# Usage:
#   frontmatter-backfill.sh                 # Scan entire vault
#   frontmatter-backfill.sh --file <path>   # Fix single file
#   frontmatter-backfill.sh --scan-missing  # Only fix notes with missing fields

set -e

VAULT_PATH="${VAULT_PATH:-.}"
CLAUSIDIAN="${CLAUSIDIAN:-$(which clausidian)}"
REPORT_FILE="$VAULT_PATH/logs/frontmatter-backfill-$(date +%Y-%m-%d).log"
SINGLE_FILE=""
SCAN_MODE="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      SINGLE_FILE="$2"
      shift 2
      ;;
    --scan-missing)
      SCAN_MODE="missing"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

mkdir -p "$(dirname "$REPORT_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$REPORT_FILE"
}

infer_domain_from_tags() {
    local tags="$1"

    if echo "$tags" | grep -qE "(claude-code|clausidian|hooks|lsp|llm|agent|prompt)" ; then
        echo "ai-engineering"
    elif echo "$tags" | grep -qE "(obsidian|vault|para|note-taking|pka)" ; then
        echo "knowledge-management"
    elif echo "$tags" | grep -qE "(github|open-source|release|license)" ; then
        echo "open-source"
    elif echo "$tags" | grep -qE "(machine|os|dev-tools|system)" ; then
        echo "dev-environment"
    elif echo "$tags" | grep -qE "(csm|pretext|gospel|yololab|project)" ; then
        echo "project-specific"
    else
        echo ""
    fi
}

fix_note() {
    local note_slug="$1"
    local domain="$2"
    local maturity="$3"

    # Update via clausidian
    [[ -n "$domain" ]] && "$CLAUSIDIAN" update --note "$note_slug" --domain "$domain" --vault "$VAULT_PATH" 2>/dev/null && log "  ✅ $note_slug: domain=$domain"
    [[ -n "$maturity" ]] && "$CLAUSIDIAN" update --note "$note_slug" --maturity "$maturity" --vault "$VAULT_PATH" 2>/dev/null && log "  ✅ $note_slug: maturity=$maturity"
}

# ==================== Main ====================

if [ -n "$SINGLE_FILE" ]; then
    # Fix a single file
    if [[ ! "$SINGLE_FILE" == /* ]]; then
        SINGLE_FILE="$VAULT_PATH/$SINGLE_FILE"
    fi

    if [ -f "$SINGLE_FILE" ]; then
        log "🔧 Backfilling: $(basename $SINGLE_FILE)"

        # Extract note slug from path
        slug=$(basename "$SINGLE_FILE" .md)

        # Check file for missing fields
        if ! grep -q "^domain:" "$SINGLE_FILE" 2>/dev/null; then
            # Infer from tags
            tags=$(grep "^tags:" "$SINGLE_FILE" | head -1 | sed 's/^tags: //' || echo "")
            domain=$(infer_domain_from_tags "$tags")
            [ -z "$domain" ] && domain="project-specific"
            fix_note "$slug" "$domain" ""
            log "  Added domain: $domain"
        fi

        if ! grep -q "^maturity:" "$SINGLE_FILE" 2>/dev/null; then
            fix_note "$slug" "" "seed"
            log "  Added maturity: seed"
        fi
    fi
else
    # Scan all notes
    log "🔍 Frontmatter Backfill — $(date)"
    log "Vault: $VAULT_PATH"
    log "Mode: $SCAN_MODE"
    log ""

    NOTES_JSON=$("$CLAUSIDIAN" list --json --vault "$VAULT_PATH" 2>/dev/null || echo "[]")
    FIXED_COUNT=0

    echo "$NOTES_JSON" | jq -r '.[] | "\(.file)|\(.domain)|\(.maturity)|\(.tags | join(","))"' 2>/dev/null | while IFS='|' read -r file domain maturity tags; do
        [ -z "$file" ] && continue

        # Check for missing fields
        needs_fix=false
        domain_fix=""
        maturity_fix=""

        if [ -z "$domain" ] || [ "$domain" = "null" ] || [ "$domain" = '""' ]; then
            needs_fix=true
            domain_fix=$(infer_domain_from_tags "$tags")
            [ -z "$domain_fix" ] && domain_fix="project-specific"
        fi

        if [ -z "$maturity" ] || [ "$maturity" = "null" ] || [ "$maturity" = '""' ]; then
            needs_fix=true
            maturity_fix="seed"
        fi

        if [ "$needs_fix" = true ]; then
            log "📝 $file"
            [ -n "$domain_fix" ] && "$CLAUSIDIAN" update --note "$file" --domain "$domain_fix" --vault "$VAULT_PATH" 2>/dev/null && log "  ✅ domain=$domain_fix" && ((FIXED_COUNT++))
            [ -n "$maturity_fix" ] && "$CLAUSIDIAN" update --note "$file" --maturity "$maturity_fix" --vault "$VAULT_PATH" 2>/dev/null && log "  ✅ maturity=$maturity_fix" && ((FIXED_COUNT++))
        fi
    done

    log ""
    log "✅ Backfill complete. Report: $REPORT_FILE"
fi
