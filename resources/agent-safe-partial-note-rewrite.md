---
title: "agent-safe-partial-note-rewrite"
type: resource
subtype: learning
tags: [agent, obsidian, vault, rewrite, protocol, clausidian, rest-api]
created: "2026-04-06"
updated: "2026-04-06"
status: active
maturity: seedling
domain: ai-engineering
summary: "Pattern for AI agents to safely rewrite specific heading sections in Obsidian notes without touching human-authored content."
source: "feat/agent-rewrite-protocol (scripts/windows-nodejs-rewriter.js)"
related: [[[harness-engineering-research]], [[claude-agent-sdk-api]], [[architecture-lessons]]]
relation_map: ""
---

# agent-safe-partial-note-rewrite

## Problem

AI agents that rewrite entire notes destroy human-authored content. The common pattern of `GET note → LLM rewrite → PUT note` is too destructive. Need heading-level granularity with permission enforcement.

## Solution: agent-rewrite protocol

Use Obsidian Local REST API's heading-targeted PATCH to update only one section. Gate writes behind a two-level permission system so locked headings are never modified.

**Pipeline:**
```
clausidian search → GET note → permission check → document-map verify
→ GET heading content → LLM → PATCH heading → PATCH frontmatter + Agent Log
```

**Implementation:** `scripts/windows-nodejs-rewriter.js` + `scripts/llm-adapter.js`

## Permission system (two levels)

1. **Global lock** (`RISK_POLICY.lockedHeadings` in code): `人類判斷區`, `決策紀錄`, `原始摘錄` — always blocked, no override
2. **Per-note lock** (frontmatter `human_locked_headings` array): user-defined per note, blocks `replace` mode
3. **Machine-writable** (frontmatter `machine_writable_headings`): opt-in list; required for `--mode replace`

Template: `templates/t-rewrite-target.md`

## Modes

| Mode | Behavior | When to use |
|------|----------|-------------|
| `draft` | append only (always) | first run, uncertain content |
| `replace` | replace if confidence ≥ 0.8, else downgrade to append | updating established sections |
| `append` | always append | cumulative logs, changelogs |

## Key technical decisions

**`https.request()` not `fetch`:** Node 24's native fetch silently ignores `agent` options — `rejectUnauthorized:false` does nothing. Use `https.request()` for Obsidian's self-signed cert (same pattern as `.claude/lib/github-api.js`).

**`shell: true` on spawnSync:** `npm bin -g` removed in npm 9+. On Windows, `spawnSync("clausidian")` without `shell: true` can't resolve `.cmd` extensions. Always use `shell: true` when calling global npm binaries on Windows.

**`Target` header format — `NoteName::HeadingName`:** Obsidian Local REST API 3.x expects the full path format (same as document-map output), not just the bare heading name. Bare names return 404. Derive `noteName` from vault path by stripping directory and `.md` extension.

**`Content-Type: text/markdown` (no charset):** Adding `; charset=utf-8` causes the plugin's body parser to receive `undefined` (500 error). Use bare `text/markdown`.

**`Create-Target-If-Missing: true`:** Used for Agent Log heading creation — avoids a two-step POST/PATCH workaround.

## Confidence scoring

```
rewritten.length < 20  → 0.45  (too short, likely garbage)
mode === "draft"        → 0.9   (safe to append regardless)
no existing content     → 0.72  (first write, lower confidence)
default                 → 0.84  (replace with existing content)
```

If confidence < 0.8 and mode is `replace`, downgrades to `append`.

## Deferred validation

**已驗證（2026-04-06，Obsidian Local REST API v3.6.0）。** 發現並修復三個 live API bugs：

1. `document-map` 回傳字串陣列 `"NoteName::HeadingName"`，非 `{heading: string}` 物件 → `verifyHeadingExists` 解析邏輯已修正
2. `Target` header 需用 `NoteName::HeadingName` 全路徑，裸 heading 名回傳 404 → 新增 `headingTarget()` helper
3. `Content-Type: text/markdown; charset=utf-8` 導致 plugin body parser 收到 `undefined`（500）→ 改用裸 `text/markdown`

所有 REST API 路徑（GET note、GET document-map、GET heading、PATCH heading、PATCH frontmatter）在真實 Obsidian 上均驗證通過。

## Usage

```bash
# Dry-run (no Obsidian needed, only ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=sk-xxx LLM_COMMAND="node scripts/llm-adapter.js" \
  node scripts/windows-nodejs-rewriter.js \
    --query "note-title" --heading "Agent更新區" --mode draft --dry-run

# Real run (Obsidian must be open)
OLR_API_KEY=xxx ANTHROPIC_API_KEY=sk-xxx LLM_COMMAND="node scripts/llm-adapter.js" \
  node scripts/windows-nodejs-rewriter.js \
    --query "note-title" --heading "Agent更新區" --mode draft
```

## References

- Protocol design: `docs/agent-rewrite-protocol.md`
- PR: sooneocean/dev-vault#4
- E2E validation: 2026-04-06 passed