---
title: "Session-Stop Wrapper: Bypassing CLI Limitations with Stdin Extraction"
date: 2026-03-29
category: harness-automation
problem_type: missing-capability
severity: moderate
root_cause: "obsidian-agent sessionStop() only reads stop_reason from stdin JSON, ignoring last_assistant_message"
solution_type: wrapper-script
technologies: [bash, jq, obsidian-agent, claude-code-hooks]
time_to_solve: "~30 min (brainstorm→plan→work full cycle)"
---

# Session-Stop Wrapper: Bypassing CLI Limitations with Stdin Extraction

## Problem

`obsidian-agent hook session-stop` receives full stdin JSON from Claude Code's Stop hook (including `last_assistant_message`, `session_id`, `cwd`), but `sessionStop()` only extracts the `stop_reason` field. This results in journal entries containing only `[HH:MM:SS] Session ended (user_exit)` — no activity summary.

Scope boundary: cannot modify obsidian-agent CLI core (changes should be validated in vault first, then upstreamed).

## Solution

**Wrapper script** (`scripts/session-stop-wrapper.sh`) that:
1. Reads stdin JSON directly (bypassing CLI's limited extraction)
2. Extracts `last_assistant_message` via `jq`, truncates to 300 chars
3. Collapses newlines to spaces for single-line journal entry
4. Calls `obsidian-agent journal` (ensure entry exists) then `obsidian-agent patch --heading "Records" --append`
5. Three-level fallback: `last_assistant_message` → `git diff --stat` → `Session ended ($STOP_REASON)`

**Settings.json changes:**
- Replace direct CLI call with wrapper script
- Add second hook: `obsidian-agent sync` (auto-rebuild indices)
- Both hooks have independent 10s timeouts

## Key Insights

1. **Wrapper > CLI patch for validation**: Writing a bash wrapper let us validate the approach in-vault before committing to a CLI code change. Lower risk, faster iteration.
2. **`patch --append` is reliable**: `obsidian-agent patch --heading "Records" --append "..."` correctly finds the heading and appends within section boundaries. Deferred question resolved during implementation.
3. **Windows Git Bash stdin works**: `jq` + stdin piping on Git Bash (Windows) is stable. The "deferred to implementation" concern was unfounded.
4. **Slash commands as lightweight bridges**: `.claude/commands/*.md` files are instructions for Claude, not executable scripts. This makes them the ideal bridge between CE outputs and vault — no plugin modification needed.
5. **Hook array ordering is guaranteed**: Same matcher group hooks execute sequentially, so journal-then-sync ordering is reliable.

## What Would I Do Differently

- Test stdin piping in the actual hook context earlier (Bash tool pipe behavior differs from real hook execution)
- Specify append vs prepend ordering in the plan explicitly (avoids UX surprise)

## Related

- Plan: `docs/plans/2026-03-29-002-feat-obsidian-agent-efficiency-plan.md`
- Requirements: `docs/brainstorms/2026-03-29-obsidian-agent-efficiency-requirements.md`
- Wrapper script: `scripts/session-stop-wrapper.sh`
