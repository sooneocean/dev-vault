---
title: "Compound Engineering Plugin"
type: resource
tags: [claude-code, compound-engineering, plugins, workflow, planning]
created: "2026-03-29"
updated: "2026-03-30"
status: active
subtype: reference
maturity: growing
domain: ai-engineering
summary: "Claude Code 外掛 — 累積式工程工作流，含規劃、審查、知識複利六大指令"
source: "https://github.com/EveryInc/compound-engineering-plugin"
related: ["[[claude-code-configuration]]", "[[claude-code-dev-tools]]", "[[2026-03-29]]", "[[prompt-engineering-research]]", "[[context-engineering-research]]", "[[harness-engineering-research]]", "[[compound-engineering-research]]", "[[context-engineering-hygiene]]"]
relation_map: "compound-engineering-research:documents, harness-engineering-research:extends"
---

# Compound Engineering Plugin

由 [Every Inc](https://every.to) 開發的 Claude Code 外掛，MIT 授權。

## 核心理念

每一次工程工作都應該讓下一次更容易，而非更難。80% 規劃與審查、20% 執行。

## 工作流

```
Brainstorm → Plan → Work → Review → Compound → Repeat
```

| 指令 | 用途 |
|------|------|
| `/ce:ideate` | 發散式腦力激盪，找高影響改進 |
| `/ce:brainstorm` | 探索需求與方向（主要入口） |
| `/ce:plan` | 將想法轉為詳細實作計畫 |
| `/ce:work` | 用 worktree + 任務追蹤執行 |
| `/ce:review` | 多 agent 分層代碼審查 |
| `/ce:compound` | 記錄學習成果，累積知識 |

## 安裝

```bash
/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering
```

## 安裝後變化

- Plugins: 11 → 12
- Agents: 5 → 52（大量專業化 review、research、workflow agents）
- MCP Servers: 6 → 7（新增 context7 — 即時查詢 library 文件）

## 附帶功能

- 52 個專業 agents（adversarial reviewer, security sentinel, performance oracle 等）
- context7 MCP — 即時查詢任何 library/framework 的最新文件
- 支援多平台：Cursor, Codex, Gemini CLI, Copilot, Windsurf 等

## Related

- [[claude-code-configuration]]
- [[claude-code-dev-tools]]
