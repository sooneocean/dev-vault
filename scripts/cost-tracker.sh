#!/bin/bash
# cost-tracker.sh — Stop hook
# Appends per-session token usage to ~/.claude/cost-log.jsonl.
# Warns on session cost thresholds (level transitions only).
#
# JSONL format per entry:
#   {"timestamp":"...","session_id":"...","model":"...","input_tokens":N,"output_tokens":N,"cost_usd":N}
#
# Thresholds (USD):
#   Level 1: $0.50
#   Level 2: $2.00
#   Level 3: $5.00
#
# Adapted from projects/_tools/claude-session-manager-new/.claude/hooks/cost-tracker.sh

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
MODEL=$(echo "$INPUT" | jq -r '.model // "unknown"' 2>/dev/null)
INPUT_TOKENS=$(echo "$INPUT" | jq -r '.usage.input_tokens // 0' 2>/dev/null)
OUTPUT_TOKENS=$(echo "$INPUT" | jq -r '.usage.output_tokens // 0' 2>/dev/null)

[ -z "$SESSION_ID" ] && exit 0
command -v jq >/dev/null 2>&1 || exit 0

# Cost model (USD per 1M tokens) — update as pricing changes
case "$MODEL" in
  *opus-4*|*opus*4*)   INPUT_RATE="15"; OUTPUT_RATE="75" ;;
  *sonnet-4*|*sonnet*) INPUT_RATE="3";  OUTPUT_RATE="15" ;;
  *haiku-4*|*haiku*)   INPUT_RATE="0.8"; OUTPUT_RATE="4" ;;
  *)                    INPUT_RATE="3";  OUTPUT_RATE="15" ;;
esac

# Calculate cost (bc for floating point)
if command -v bc >/dev/null 2>&1; then
  COST=$(echo "scale=6; ($INPUT_TOKENS * $INPUT_RATE + $OUTPUT_TOKENS * $OUTPUT_RATE) / 1000000" | bc 2>/dev/null || echo "0")
else
  COST="0"
fi

COSTS_FILE="$HOME/.claude/cost-log.jsonl"
mkdir -p "$(dirname "$COSTS_FILE")"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")
echo "{\"timestamp\":\"$TIMESTAMP\",\"session_id\":\"$SESSION_ID\",\"model\":\"$MODEL\",\"input_tokens\":$INPUT_TOKENS,\"output_tokens\":$OUTPUT_TOKENS,\"cost_usd\":$COST}" >> "$COSTS_FILE"

# Session total from log
SESSION_TOTAL=$(grep "\"session_id\":\"$SESSION_ID\"" "$COSTS_FILE" 2>/dev/null \
  | jq -s '[.[].cost_usd] | add // 0' 2>/dev/null || echo "0")

# Threshold state
STATE_FILE="/tmp/.claude_cost_tracker_${SESSION_ID}"
WARNED_LEVEL=0
[ -f "$STATE_FILE" ] && WARNED_LEVEL=$(cat "$STATE_FILE" 2>/dev/null || echo 0)

CURRENT_LEVEL=0
if command -v bc >/dev/null 2>&1; then
  (( $(echo "$SESSION_TOTAL >= 5.0" | bc -l 2>/dev/null || echo 0) )) && CURRENT_LEVEL=3
  (( $(echo "$SESSION_TOTAL >= 2.0" | bc -l 2>/dev/null || echo 0) )) && [ $CURRENT_LEVEL -lt 3 ] && CURRENT_LEVEL=2
  (( $(echo "$SESSION_TOTAL >= 0.5" | bc -l 2>/dev/null || echo 0) )) && [ $CURRENT_LEVEL -lt 2 ] && CURRENT_LEVEL=1
fi

echo "$CURRENT_LEVEL" > "$STATE_FILE"

if [ "$CURRENT_LEVEL" -gt 0 ] && [ "$CURRENT_LEVEL" -gt "$WARNED_LEVEL" ]; then
  case $CURRENT_LEVEL in
    1) echo "[COST] Session: \$${SESSION_TOTAL} — 已超過 \$0.50，注意成本。" ;;
    2) echo "[COST ⚠️] Session: \$${SESSION_TOTAL} — 已超過 \$2.00，建議縮小操作範圍。" ;;
    3) echo "[COST 🚨] Session: \$${SESSION_TOTAL} — 已超過 \$5.00！考慮切換至 sonnet 或 /clear 重啟。" ;;
  esac
fi

exit 0
