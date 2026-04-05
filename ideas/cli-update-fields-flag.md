---
title: "cli-update-fields-flag"
type: idea
tags: [clausidian, frontmatter, brainstorm, future, ai-engineering]
created: "2026-03-29"
updated: "2026-04-03"
status: "archived"
maturity: seed
domain: knowledge-management
summary: "Add --fields flag to obsidian-agent updateNote() to INSERT new frontmatter keys, not just update existing ones"
related: ["[[dexg16-ai-coding-tools]]", "[[improvement-2026-03-29-001]]", "[[session-stop-wrapper-learning]]", "[[research-update-mode]]"]
relation_map: "research-update-mode:extends"
---

# cli-update-fields-flag

## The Idea

Extend `obsidian-agent`'s `updateNote()` function to accept a `--fields` flag that can INSERT new frontmatter keys into an existing note, not just UPDATE values of keys that already exist. For example: `obsidian-agent update "note-name" --fields "subtype:research, domain:ai-engineering"` would add `subtype` and `domain` to the frontmatter even if those keys were not present at creation time.

## Why

During the Plan 004 vault schema migration (2026-03-30), all 31 notes needed new frontmatter fields (`subtype`, `maturity`, `domain`, `relation_map`). The CLI's `updateNote()` could not handle this — every note required direct file editing. This makes schema evolution painful and error-prone. A `--fields` flag would let agents and scripts migrate frontmatter programmatically.

## Next Steps

- [ ] Audit `vault.mjs` `updateNote()` implementation to understand current key-matching logic
- [ ] Design the `--fields` API: flag syntax, conflict resolution (skip vs. overwrite existing)
- [ ] Implement and add tests for INSERT behavior
- [ ] Open PR on `redredchen01/obsidian-agent` with the change
