---
title: "Context Engineering Hygiene"
type: resource
subtype: "learning"
tags: [knowledge-management, auto-memory-migration, context-engineering]
created: "2026-03-30"
updated: "2026-03-30"
status: active
maturity: mature
domain: "ai-engineering"
summary: "Actionable context hygiene rules — when to compact, when to use subagents, plugin overhead awareness"
source: ""
related: ["[[dev-vault-status]]", "[[architecture-lessons]]", "[[tech-research-squad]]", "[[context-engineering-research]]", "[[compound-engineering-plugin]]", "[[benchmark-first-rule]]", "[[toolchain-reference]]", "[[claude-agent-sdk-api]]"]
relation_map: ""
---

# Context Engineering Hygiene

## Overview

Actionable context hygiene rules learned from research and hands-on experience. These rules are codified in the global CLAUDE.md and enforced by agent behavior.

## Key Points

### Manual /compact at 70% beats auto-compact at 83.5%

Manually compacting at 70% with explicit preservation instructions gives better results than waiting for auto-compact. Auto-compact at 83.5% leaves only ~33K tokens for the compaction buffer, resulting in lossy summaries.

**Evidence:** HyperDev research and Anthropic docs confirm quality degrades above 75% usage. The 70% manual threshold is from [[csm-architecture]] design and community best practice.

**Rule:** Suggest /compact at natural breakpoints (feature complete, task switch). After 2+ compacts in one session, suggest /clear instead — summaries compound in abstraction.

### Subagent isolation: 8x cleaner context

Using subagents for exploration reduces main context noise from 91% to 24% (Jason Liu research). The quantitative threshold: use subagent when estimated output > 50K tokens OR reading > 3 files over 500 lines.

**Why:** Main context pollution from exploration is the #1 cause of quality degradation in long sessions.

**Rule:** Stack traces, verbose logs, broad codebase searches → always subagent. Quick questions with answers already in context → /btw or main context.

### 12 plugins consume ~10-15K tokens in tool definitions

Plugin tool definitions are loaded at session start regardless of whether they are used. The 6 "occasional" plugins (playwright, chrome-devtools, typescript-lsp, pyright-lsp, review-loop, cartographer) contribute to this overhead even in vault-only sessions.

**Evidence:** Measured from settings.json plugin inventory on 2026-03-29. Exact per-plugin breakdown pending /cost measurement.

**Rule:** Consider plugin profiles for different work types (vault-only, web-dev, python-dev) as a future optimization. Do not disable anything without data.

## Notes

## Related

