---
title: "Toolchain Reference"
type: resource
subtype: "reference"
tags: [knowledge-management, auto-memory-migration]
created: "2026-03-30"
updated: "2026-03-30"
status: active
maturity: growing
domain: "dev-environment"
summary: "External repos, tools, plugins and config paths used in this project"
source: ""
related: ["[[dev-vault-status]]", "[[architecture-lessons]]", "[[benchmark-first-rule]]", "[[context-engineering-hygiene]]", "[[improvement-2026-03-29-001]]", "[[claude-agent-sdk-api]]"]
relation_map: ""
---

# Toolchain Reference

## Overview

Central reference for all external repos, tools, plugins and config paths used in this project.

## Key Points

### Authored Repos

- **[[obsidian-agent]]**: github.com/redredchen01/obsidian-agent — MCP-based Obsidian CLI (v0.7.0, PR #1 pending)
- **session-wrap-skill**: github.com/redredchen01/session-wrap-skill — Universal agent memory persistence (v3.5)

### Installed Skills & Plugins

- **Compound Engineering Plugin**: github.com/EveryInc/compound-engineering-plugin — 52 agents, 6 workflows (/ce:ideate, brainstorm, plan, work, review, compound)
- **session-wrap**: ~/.claude/skills/session-wrap/SKILL.md (global)
- **obsidian skill**: ~/.claude/skills/obsidian/ (global)

### Key Config Paths

| Path | Purpose |
|------|---------|
| /c/DEX_data/Claude Code DEV | Vault root |
| ~/.claude/CLAUDE.md | Global CLAUDE.md |
| vault root CLAUDE.md | Project CLAUDE.md |
| ~/.claude/settings.json | Global settings |
| scripts/session-stop-wrapper.sh | Session-stop wrapper |

## Notes

## Related

