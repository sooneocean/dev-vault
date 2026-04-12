---
title: List notes in the knowledge base
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-06
status: active
maturity: growing
domain: knowledge-management
summary: "Lists notes in the vault knowledge base with optional filtering."
---

List notes in the knowledge base.

Usage: `[type] [--status STATUS] [--tag TAG] [--recent N]`

Run: `clausidian list [type] [--status STATUS] [--tag TAG] [--recent N]`

If the CLI is not available:
1. Parse filter parameters
2. Scan frontmatter across all note directories
3. Apply filters (type, status, tag, recent days)
4. Display as table: file, title, type, status, summary, updated
5. Sort by updated date descending
6. Show stats at the end

$ARGUMENTS
