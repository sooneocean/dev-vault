---
title: "{{PRODUCT_NAME}} — Version Tracker"
type: project
tags: [version-tracking, product-iteration]
created: "{{DATE}}"
updated: "{{DATE}}"
status: active
maturity: mature
domain: project-specific
summary: "Central version and iteration history tracker for {{PRODUCT_NAME}}"
current_version: "{{INITIAL_VERSION}}"
last_release_date: "{{DATE}}"
related: []
relation_map: ""
---

# {{PRODUCT_NAME}} — Version Tracker

## Current Version

**Version:** {{INITIAL_VERSION}}

**Released:** {{DATE}}

**Description:** {{RELEASE_DESCRIPTION}}

## Last Release Date

{{DATE}}

## Completed Features (Current Cycle)

{{FEATURES_LIST}}

## Iteration History

Ordered by release date (newest first).

### Latest Iteration

- [[{{INITIAL_VERSION}} — Iteration {{DATE}}|{{ITERATION_NOTE_LINK}}]]

### Previous Iterations

{{PREVIOUS_ITERATIONS}}

## Next Planned Features

{{NEXT_FEATURES}}

## Release Checklist

- [ ] All approved features merged to main
- [ ] All tests passing
- [ ] No blocking issues
- [ ] Changelog reviewed and finalized
- [ ] Version bump approved
- [ ] GitHub release created with changelog
- [ ] Vault iteration note updated
- [ ] Product version tracker updated

## Notes

- Version source of truth: Git tag (GitHub releases)
- Iteration history: Stored as separate vault notes (one per iteration)
- Proposals and selections: Recorded in iteration notes
- Changelog format: Markdown, categories: Breaking Changes / Features / Bug Fixes
