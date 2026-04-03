---
title: Untitled
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

Search notes in the knowledge base.

Usage: `<keyword> [--type TYPE] [--tag TAG] [--status STATUS]`

Run: `obsidian-agent search "<keyword>" [--type TYPE] [--tag TAG] [--status STATUS]`

If the CLI is not available:
1. Parse search parameters
2. Grep across the vault (exclude `.obsidian/`, `.git/`, `templates/`)
3. Filter by type/tag/status if specified
4. Show results: filename, summary, matching lines
5. Limit to top 10 most relevant

$ARGUMENTS
