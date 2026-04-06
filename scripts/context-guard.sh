#!/bin/bash
# context-guard.sh — PostToolUse hook (all tools)
# Monitors context pressure via transcript size + tool call count.
# Warns only on level transitions to avoid spam.
#
# Thresholds:
#   Level 1 (Notice):   transcript > 300KB OR 28+ calls
#   Level 2 (Warning):  transcript > 500KB OR 38+ calls
#   Level 3 (Critical): transcript > 700KB OR 50+ calls
#
# Adapted from projects/_tools/claude-session-manager-new/.claude/hooks/context-guard.sh

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)

[ -z "$SESSION_ID" ] && exit 0

STATE_FILE="/tmp/.claude_ctx_guard_${SESSION_ID}"

CALLS=0
WARNED_LEVEL=0
if [ -f "$STATE_FILE" ]; then
  CALLS=$(sed -n '1p' "$STATE_FILE" 2>/dev/null || echo 0)
  WARNED_LEVEL=$(sed -n '2p' "$STATE_FILE" 2>/dev/null || echo 0)
  CALLS=$((CALLS + 0))
  WARNED_LEVEL=$((WARNED_LEVEL + 0))
fi
CALLS=$((CALLS + 1))

TRANSCRIPT_KB=0
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  TRANSCRIPT_BYTES=$(wc -c < "$TRANSCRIPT" 2>/dev/null | tr -d ' ')
  TRANSCRIPT_KB=$((TRANSCRIPT_BYTES / 1024))
fi

LEVEL=0
if [ "$TRANSCRIPT_KB" -gt 700 ] || [ "$CALLS" -ge 50 ]; then
  LEVEL=3
elif [ "$TRANSCRIPT_KB" -gt 500 ] || [ "$CALLS" -ge 38 ]; then
  LEVEL=2
elif [ "$TRANSCRIPT_KB" -gt 300 ] || [ "$CALLS" -ge 28 ]; then
  LEVEL=1
fi

printf "%d\n%d\n" "$CALLS" "$LEVEL" > "$STATE_FILE"

if [ "$LEVEL" -gt 0 ] && [ "$LEVEL" -gt "$WARNED_LEVEL" ]; then
  case $LEVEL in
    1)
      echo "[CTX-GUARD] transcript=${TRANSCRIPT_KB}KB calls=${CALLS} — Context 使用量偏高，控制後續操作規模。"
      ;;
    2)
      echo "[CTX-GUARD ⚠️] transcript=${TRANSCRIPT_KB}KB calls=${CALLS} — 建議執行 /compact 後繼續。"
      ;;
    3)
      echo "[CTX-GUARD 🚨] transcript=${TRANSCRIPT_KB}KB calls=${CALLS} — 立即 /compact！避免繼續大型 Read/Write！"
      ;;
  esac
fi

exit 0
