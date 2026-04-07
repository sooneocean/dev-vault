---
title: Inbox
type: inbox
note_class: structural
tags: [inbox]
created: 2026-04-06
updated: 2026-04-06
status: active
summary: Unprocessed fleeting notes. Process within 7 days — upgrade to literature or permanent, or discard.
---

# Inbox

ZK fleeting notes awaiting processing. Run `clausidian stale` to surface aging captures.

## Processing Rules

1. Expand into `resources/literature/` if sourced from an external document
2. Distill into `resources/permanent/` if it's a single atomic idea
3. Route to a project note if it's an action item
4. Discard if no longer relevant

```bash
clausidian stale    # Find inbox notes older than 7 days
clausidian search "keyword"  # Check if related note already exists
```
