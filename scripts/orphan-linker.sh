#!/bin/bash
# orphan-linker.sh — Automatic orphan note linking
# Finds isolated notes and attempts to establish semantic connections
# via clausidian's automated linking algorithm.

set -e

VAULT_PATH="${VAULT_PATH:-.}"
CLAUSIDIAN="${CLAUSIDIAN:-$(which clausidian)}"
REPORT_FILE="$VAULT_PATH/logs/orphan-linker-$(date +%Y-%m-%d).log"
DRY_RUN=true

# Parse arguments
for arg in "$@"; do
  [[ "$arg" == "--fix" ]] && DRY_RUN=false
done

mkdir -p "$(dirname "$REPORT_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$REPORT_FILE"
}

# ==================== Main ====================

log "🔗 Orphan Linking — $(date)"
log "Vault: $VAULT_PATH"
log "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY_RUN' || echo 'APPLY_FIXES')"
log ""

# Get vault stats
STATS_JSON=$("$CLAUSIDIAN" stats --json --vault "$VAULT_PATH" 2>/dev/null || echo '{}')
ORPHAN_COUNT=$(echo "$STATS_JSON" | jq '.orphan_count // 0' 2>/dev/null || echo "0")

if [ "$ORPHAN_COUNT" = "0" ] || [ "$ORPHAN_COUNT" = "null" ]; then
    log "✅ No orphan notes found"
    exit 0
fi

log "Found $ORPHAN_COUNT orphan notes"
log ""

# Get all notes list to find orphans
NOTES_JSON=$("$CLAUSIDIAN" list --json --vault "$VAULT_PATH" 2>/dev/null || echo "[]")

# Count links per note and identify orphans
ORPHANS=()
LINKED_COUNT=0

echo "$NOTES_JSON" | jq -r '.[] | "\(.file)|\(.related | length)"' 2>/dev/null | while IFS='|' read -r file related_count; do
    [ -z "$file" ] && continue

    # Orphan = 0 related links
    if [ "$related_count" = "0" ] || [ "$related_count" = "null" ]; then
        ORPHANS+=("$file")

        log "🔗 Attempting to link: $file"

        if [ "$DRY_RUN" = false ]; then
            # Run clausidian link on this specific note
            NEW_LINKS=$("$CLAUSIDIAN" link --note "$file" --vault "$VAULT_PATH" 2>/dev/null | grep -c "Created" || echo "0")
            if [ "$NEW_LINKS" -gt 0 ]; then
                log "  ✅ Created $NEW_LINKS links"
                ((LINKED_COUNT++))
            else
                log "  ℹ️  No suitable links found"
            fi
        else
            log "  [DRY_RUN] Would attempt linking"
        fi
    fi
done

log ""
log "📊 Results:"
log "  Orphans processed: ${#ORPHANS[@]}"
log "  Links created: $LINKED_COUNT"

if [ "$DRY_RUN" = true ] && [ "${#ORPHANS[@]}" -gt 0 ]; then
    log ""
    log "💡 Run with --fix flag to apply linking:"
    log "   $0 --fix"
fi

log ""
log "✅ Orphan linking complete. Report: $REPORT_FILE"
