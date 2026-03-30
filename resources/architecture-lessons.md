---
title: "Architecture Lessons"
type: resource
subtype: "learning"
tags: [knowledge-management, auto-memory-migration, claude-code-hooks]
created: "2026-03-30"
updated: "2026-03-30"
status: active
maturity: mature
domain: "ai-engineering"
summary: "Critical lessons about Stop hooks, global config safety, and slash command nature"
source: ""
related: ["[[dev-vault-status]]", "[[context-engineering-hygiene]]", "[[benchmark-first-rule]]", "[[toolchain-reference]]", "[[claude-agent-sdk-api]]"]
relation_map: ""
---

# Architecture Lessons

## Overview

Critical architectural lessons learned while building Claude Code workflows. These constraints are non-obvious and have caused wasted effort when violated.

## Key Points

### Stop hooks cannot invoke Claude reasoning

Stop hooks are shell commands executed AFTER the Claude session ends. Claude is NOT available in Stop hooks. Any logic requiring Claude's reasoning (analysis, summarization, decision-making) must run in an active session via slash commands or explicit user invocation.

**Why:** Discovered during /improve planning. Original design had a Stop hook for signal collection where "Claude reviews the session" — feasibility review (0.92 confidence) caught this as architecturally impossible.

**Rule:** Never design features that assume Claude is available in lifecycle hooks. All intelligence must be on-demand within active sessions.

### ~/.claude/ is NOT a git repo

Global config directory has no version control. Cannot use git revert for rollback.

**Why:** Feasibility review (0.95 confidence) verified this during /improve planning.

**Rule:** Use layered rollback: git for project-level configs (in vault repo), .bak file backup for global configs (settings.json.bak.YYYY-MM-DD).

### Slash commands are prompt templates, not scripts

.claude/commands/*.md files are prompt templates injected into active Claude sessions. They are NOT standalone scripts and cannot be executed outside a session.

**Rule:** Design slash commands as instructions for Claude to follow, not as executable scripts.

## Notes

## Related

