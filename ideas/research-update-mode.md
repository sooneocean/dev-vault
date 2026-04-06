---
title: "research-update-mode"
type: idea
tags: [clausidian, diff-tracking, brainstorm, future, ai-engineering]
created: "2026-03-29"
updated: "2026-04-03"
status: "archived"
maturity: seed
domain: knowledge-management
summary: "Add --update flag to obsidian-agent research command to diff against previous research and surface changes"
related: ["[[tech-research-squad]]", "[[research-mcp-model-context-protocol-2026-03-29]]", "[[cli-update-fields-flag]]"]
relation_map: "tech-research-squad:extends"
---

# research-update-mode

## The Idea

Add an `--update` mode to the `obsidian-agent research` command. When invoked with `--update`, the command reads the existing research note, re-runs the same GitHub/web queries, and produces a structured diff highlighting what changed since the last research (new repos, updated star counts, new issues, deprecated projects, etc.).

## Why

Currently, `research` always creates a fresh note. Over time, technology landscapes shift — repos gain traction, new alternatives appear, maintainers abandon projects. Without a diffing mechanism, the only way to track evolution is to manually compare two research notes side by side. An `--update` mode turns research notes into living documents and makes trend detection automatic.

## Next Steps

- [ ] Design the diff output format (inline annotations vs. separate "Changes" section)
- [ ] Determine storage for previous snapshot (frontmatter hash, sidecar file, or git diff)
- [ ] Prototype on a single research note (e.g., MCP research) and validate usefulness
- [ ] Open issue on `redredchen01/obsidian-agent` if pursuing upstream
