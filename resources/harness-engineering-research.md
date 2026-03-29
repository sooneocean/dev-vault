---
title: "Harness Engineering 研究"
type: resource
tags: [harness-engineering, claude-code, mcp, hooks, plugins]
created: "2026-03-29"
updated: "2026-03-30"
status: active
subtype: research
maturity: growing
domain: ai-engineering
summary: "Harness Engineering — 設計 agent 的工具鏈、hook、plugin、MCP 架構"
source: ""
related: ["[[tech-research-squad]]", "[[prompt-engineering-research]]", "[[context-engineering-research]]", "[[compound-engineering-research]]", "[[claude-code-configuration]]", "[[compound-engineering-plugin]]"]
relation_map: "tech-research-squad:extends, compound-engineering-plugin:documents"
---

# Harness Engineering 研究

## 核心問題

如何設計 agent 的工具鏈、hook、plugin、MCP 架構，讓 AI 成為高效的工程夥伴？

## Harness 全貌（Sprint 1 盤點）

### 整體數據

| 要素 | 數量 | 說明 |
|------|------|------|
| Plugins | 14 | 含 compound-engineering, telegram, claude-mem 等 |
| Skills | 41+ | compound-engineering 提供 41 個 + 專案自訂 6 個 |
| Agents | 47 | compound-engineering 提供的專業子代理 |
| MCP Servers | 7+ | context7, obsidian-agent, playwright 等 |
| Hooks | 2 組 | Python (ruff) + JS/TS (prettier) 自動格式化 |
| LSP Servers | 2 | typescript-lsp, pyright-lsp |

### 已安裝 Plugins 清單

| Plugin | 版本 | 用途 |
|--------|------|------|
| compound-engineering | 2.58.1 | 累積式工程工作流（核心） |
| telegram | 0.0.4 | Telegram bot 整合 |
| claude-mem | 10.6.1 | 持久化記憶、計畫、時間線 |
| claude-hud | 0.0.10 | 狀態列顯示 |
| cartographer | 1.4.0 | 程式碼地圖 |
| review-loop | 1.8.0 | 審查迴圈 |
| context7 | latest | Library 文件即時查詢 |
| github | latest | GitHub 整合 |
| typescript-lsp | 1.0.0 | TypeScript 語言伺服器 |
| pyright-lsp | 1.0.0 | Python 語言伺服器 |
| playwright | latest | 瀏覽器自動化 |
| chrome-devtools-mcp | latest | Chrome DevTools |
| posthog | 1.0.0 | 分析（local only） |
| learning-output-style | latest | 輸出風格（local only） |

### Compound Engineering — Agent 分類

| 類別 | 數量 | 代表 Agents |
|------|------|------------|
| Code Review | 26 | correctness, security, performance, maintainability, adversarial... |
| Document Review | 7 | feasibility, coherence, scope-guardian, product-lens... |
| Research | 6 | best-practices, framework-docs, git-history, issue-intelligence... |
| Workflow | 4 | bug-reproduction, lint, pr-comment-resolver, spec-flow-analyzer |
| Design | 3 | design-iterator, figma-design-sync, design-implementation-reviewer |
| Documentation | 1 | ankane-readme-writer |

### Hooks（自動化）

| 觸發器 | 動作 | 檔案類型 |
|--------|------|---------|
| Write/Edit | `ruff format` + `ruff check --fix` | `.py` |
| Write/Edit | `npx prettier --write` | `.ts .tsx .js .jsx .css` |

### 關鍵設定

- Effort: high
- 權限: Bash(*), Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, mcp__* 全開
- Auto-updates: latest channel
- Enable all project MCP servers: true

## 架構觀察

1. **分層設計** — Global (settings.json, CLAUDE.md) → Project (.claude/) → Plugin → Runtime
2. **Tiered Persona Agents** — `/ce:review` 平行派出多個角色審查，最後合併去重
3. **Confidence Gating** — 審查結果附帶信心分數，可設門檻過濾
4. **Institutional Knowledge Loop** — `/ce:compound` 記錄 → `learnings-researcher` 搜尋 → 下次使用

## 迭代紀錄

### Sprint 1 — 2026-03-29

**做了什麼：** 完整盤點 harness 全貌 — 14 plugins, 47 agents, 41 skills
**學到什麼：**
- Compound Engineering 是目前最大的外掛，單獨貢獻 47 agents + 41 skills
- Hooks 只有格式化，還有很大的自動化空間
- 架構是分層的：Global → Project → Plugin → Runtime
- Agent 分類很清楚：Review (最多) > Doc Review > Research > Workflow > Design > Docs
**哪裡卡住：** 還沒實際用過 `/ce:review` 或 `/ce:plan`，不確定效果
**下次要試：** 用 `/ce:brainstorm` 或 `/ce:plan` 跑一個真實任務，體驗完整工作流
**知識複利：** 這份盤點本身就是未來快速定位工具的索引

### Sprint 2 — 2026-03-29

**做了什麼：** 完成 obsidian-agent 底層效率改進（brainstorm → plan → work 全流程）
- 建立 `scripts/session-stop-wrapper.sh` — Stop hook 自動擷取 `last_assistant_message` 寫入 journal Records
- 新增 sync hook — session 結束時自動重建 vault 索引
- 建立 `/bridge-compound` slash command — 橋接 CE compound 學習文件到 vault resources
- 建立 `/bridge-plan` slash command — 橋接 CE plan 到 vault project 筆記

**學到什麼：**
- Stop hook 的 `sessionStop()` 只讀 `stop_reason`，wrapper script 繞過此限制直接讀 stdin JSON
- `obsidian-agent patch --heading --append` 可靠追加到指定區段
- slash command 是最輕量的 CE ↔ vault 橋接方式，不需改 plugin 本身

**哪裡卡住：**
- Windows Git Bash 的 pipe stdin 行為與 file redirect 不同，需要實測確認
- journal 被多個 session 同時 patch 時可能產生意外追加（已清理）

**下次要試：**
- 實際跑一次 `/ce:compound` → `/bridge-compound` 的完整知識複利流程
- 驗證 sync hook 的索引更新時間是否在 10s timeout 內

**知識複利：** wrapper script 模式可複製到其他 hook 自動化；bridge command 模式可擴展到其他 CE 產出

## 開放問題

- Plugin 之間的互動與衝突如何管理？
- Hook 還能做什麼自動化？（lint, test, commit message validation?）→ 已實作 journal 自動化 ✓
- 如何設計自己的 MCP server？
- 47 個 agents 中哪些最值得優先掌握？
- `/ce:review` 的 tiered persona 機制具體如何運作？

## Related

- [[tech-research-squad]]
- [[claude-code-configuration]]
- [[compound-engineering-plugin]]
