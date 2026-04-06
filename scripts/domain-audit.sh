#!/bin/bash
# domain-audit.sh — Automated domain field audit and repair
# Identifies notes with missing or invalid domain values
# and suggests corrections based on tags and directory location

set -e

VAULT_PATH="${VAULT_PATH:-.}"
CLAUSIDIAN="${CLAUSIDIAN:-$(which clausidian)}"
REPORT_FILE="$VAULT_PATH/logs/domain-audit-$(date +%Y-%m-%d).log"
DRY_RUN=true
FIX_MODE=false

# Domain vocabulary (from CONVENTIONS.md)
VALID_DOMAINS=(
    "ai-engineering"
    "dev-environment"
    "open-source"
    "knowledge-management"
    "project-specific"
)

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== Functions ====================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$REPORT_FILE"
}

is_valid_domain() {
    local domain="$1"
    for valid in "${VALID_DOMAINS[@]}"; do
        [[ "$domain" == "$valid" ]] && return 0
    done
    return 1
}

infer_domain_from_tags() {
    local tags="$1"

    # Check tags and infer domain
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
        echo "unknown"
    fi
}

infer_domain_from_path() {
    local path="$1"

    # Simple directory-based heuristics
    if [[ "$path" == *"/areas/"* ]]; then
        echo "project-specific"
    elif [[ "$path" == *"/journal/"* ]]; then
        echo "knowledge-management"
    else
        echo "unknown"
    fi
}

# ==================== Main ====================

mkdir -p "$(dirname "$REPORT_FILE")"

log "🔍 Domain Audit — $(date)"
log "Vault: $VAULT_PATH"
log "Mode: DRY_RUN=$DRY_RUN, FIX=$FIX_MODE"
log ""

# Get all notes as JSON
NOTES_JSON=$("$CLAUSIDIAN" list --json 2>/dev/null || echo "[]")

if [ "$NOTES_JSON" = "[]" ]; then
    log "❌ Failed to list notes via clausidian"
    exit 1
fi

VIOLATION_COUNT=0
FIXED_COUNT=0

# Parse JSON and check each note
echo "$NOTES_JSON" | jq -r '.[] | "\(.file)|\(.domain)|\(.tags | join(","))"' 2>/dev/null | while IFS='|' read -r file domain tags; do

    # Skip if empty
    [ -z "$file" ] && continue

    # Check for missing or invalid domain
    if [ -z "$domain" ] || [ "$domain" = "null" ] || [ "$domain" = '""' ]; then
        # Infer domain
        inferred=$(infer_domain_from_tags "$tags")
        if [ "$inferred" = "unknown" ]; then
            # Fall back to path-based inference
            inferred=$(infer_domain_from_path "$file")
        fi

        log "⚠️  Missing domain: $file → inferred: $inferred (tags: $tags)"

        if [ "$FIX_MODE" = true ]; then
            "$CLAUSIDIAN" update --note "$file" --domain "$inferred" 2>/dev/null && {
                log "  ✅ Fixed: $file domain=$inferred"
                ((FIXED_COUNT++))
            } || log "  ❌ Failed to fix: $file"
        fi

        ((VIOLATION_COUNT++))
    elif ! is_valid_domain "$domain"; then
        log "❌ Invalid domain: $file (domain=$domain, valid: ${VALID_DOMAINS[*]})"

        # Try to infer replacement
        inferred=$(infer_domain_from_tags "$tags")
        if [ "$inferred" != "unknown" ]; then
            if [ "$FIX_MODE" = true ]; then
                "$CLAUSIDIAN" update --note "$file" --domain "$inferred" 2>/dev/null && {
                    log "  ✅ Corrected: $file $domain → $inferred"
                    ((FIXED_COUNT++))
                } || log "  ❌ Failed to correct: $file"
            fi
        fi

        ((VIOLATION_COUNT++))
    fi
done

log ""
log "📊 Audit Results:"
log "  Violations found: $VIOLATION_COUNT"
log "  Fixed: $FIXED_COUNT"
log ""

if [ "$DRY_RUN" = true ] && [ "$VIOLATION_COUNT" -gt 0 ]; then
    log "💡 Run with --fix flag to apply corrections:"
    log "   $0 --fix"
fi

log "✅ Audit complete. Report: $REPORT_FILE"
