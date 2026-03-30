---
title: "{{VERSION}} — Iteration {{ITERATION_DATE}}"
type: project
subtype: iteration-log
tags: []
created: "{{ITERATION_DATE}}"
updated: "{{ITERATION_DATE}}"
status: active
maturity: growing
domain: project-specific
summary: "Iteration record for version {{VERSION}}: proposals, selections, and release metadata"
version: "{{VERSION}}"
iteration_date: "{{ITERATION_DATE}}"
proposals_count: "{{PROPOSALS_COUNT}}"
selected_count: "{{SELECTED_COUNT}}"
github_release_url: ""
github_release_date: ""
related: []
relation_map: ""
---

# {{VERSION}} — Iteration {{ITERATION_DATE}}

## Proposals Generated

**Date:** {{ITERATION_DATE}}
**Version Target:** {{VERSION}}

### Proposal Details

| # | Title | Problem | Effort | Value | Rank | Status |
|---|-------|---------|--------|-------|------|--------|
{{PROPOSALS_TABLE}}

**Total Proposals:** {{PROPOSALS_COUNT}}

## Features Selected

**Date:** {{SELECTION_DATE}}
**Selected:** {{SELECTED_COUNT}} of {{PROPOSALS_COUNT}}

### Selected Features

| # | Title | GitHub Issue | Status |
|---|-------|--------------|--------|
{{SELECTED_FEATURES_TABLE}}

## Release Record

**Release Date:** {{GITHUB_RELEASE_DATE}}
**GitHub Release:** {{GITHUB_RELEASE_URL}}

### Changelog

{{CHANGELOG_BODY}}

### Version Jump

- **Previous Version:** {{PREVIOUS_VERSION}}
- **Released Version:** {{VERSION}}
- **Version Bump Reason:** {{VERSION_BUMP_REASON}}

## Iteration Notes

- Started: {{ITERATION_DATE}}
- Proposals finalized: {{SELECTION_DATE}}
- Released: {{GITHUB_RELEASE_DATE}}

## Links

- [[Product Version Tracker|projects/product-version]] — Current version tracking
- {{RELATED_ITERATION_LINKS}}
