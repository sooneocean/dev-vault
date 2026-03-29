#!/usr/bin/env bash
# session-stop-wrapper.sh — Claude Code Stop hook
# Reads stdin JSON, extracts activity summary, appends to vault journal Records.
# Falls back to git diff --stat if last_assistant_message is empty.
# Silently succeeds on any error to never block session exit.

set -o pipefail

VAULT="/c/DEX_data/Claude Code DEV"
MAX_LEN=300

# Read stdin (Claude Code pipes JSON with session metadata)
STDIN_JSON=$(cat 2>/dev/null) || STDIN_JSON=""

# Timestamp
TS=$(date +"%H:%M:%S")
TODAY=$(date +"%Y-%m-%d")

# --- Extract summary ---
SUMMARY=""

if command -v jq &>/dev/null && [ -n "$STDIN_JSON" ]; then
  # Try last_assistant_message first
  SUMMARY=$(echo "$STDIN_JSON" | jq -r '.last_assistant_message // empty' 2>/dev/null | head -c "$MAX_LEN")

  # Extract stop_reason for fallback context
  STOP_REASON=$(echo "$STDIN_JSON" | jq -r '.stop_reason // "unknown"' 2>/dev/null)
else
  STOP_REASON="unknown"
fi

# Fallback: git diff --stat if summary is empty
if [ -z "$SUMMARY" ]; then
  if [ -n "$STDIN_JSON" ] && command -v jq &>/dev/null; then
    CWD=$(echo "$STDIN_JSON" | jq -r '.cwd // empty' 2>/dev/null)
  fi
  CWD="${CWD:-$(pwd)}"

  DIFF_STAT=$(git -C "$CWD" diff --stat HEAD~1 HEAD 2>/dev/null | tail -1)
  if [ -n "$DIFF_STAT" ]; then
    SUMMARY="[git] $DIFF_STAT"
  else
    SUMMARY="Session ended ($STOP_REASON)"
  fi
fi

# Clean up: collapse newlines to spaces, trim
SUMMARY=$(echo "$SUMMARY" | tr '\n' ' ' | sed 's/  */ /g; s/^ *//; s/ *$//')

# Truncate if still too long
if [ ${#SUMMARY} -gt $MAX_LEN ]; then
  SUMMARY="${SUMMARY:0:$MAX_LEN}..."
fi

# --- Write to journal ---
APPEND_LINE="- [$TS] $SUMMARY"

# Ensure today's journal entry exists
obsidian-agent journal --vault "$VAULT" &>/dev/null || true

# Append to Records section
obsidian-agent patch "$TODAY" --heading "Records" --append "$APPEND_LINE" --vault "$VAULT" &>/dev/null || true
