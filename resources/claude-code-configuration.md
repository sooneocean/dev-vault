---
title: "Claude Code 設定"
type: resource
tags: [claude-code, config, plugins, hooks]
created: "2026-03-28"
updated: "2026-03-28"
status: active
summary: "Claude Code 的設定、外掛、Hook、MCP 伺服器與專案層級配置"
source: ""
related: ["[[claude-code-dev-tools]]", "[[claude-session-manager]]", "[[dexg16-ai-coding-tools]]", "[[csm-architecture]]", "[[dexg16-ai-stack]]", "[[dexg16-git-and-github]]"]
---

# Claude Code 設定

## 重點

### 全域設定（`~/.claude/settings.json`）

**權限（全部自動允許）：**
- Bash(*)、Read、Edit、Write、Glob、Grep、WebFetch、WebSearch
- Skill(*)、Agent(*)、mcp__*
- 額外目錄：`C:\Users\User\Projects`
- 危險模式權限提示：**已跳過**

**努力程度（Effort Level）：** high

### 外掛（11 個已啟用）

| 外掛 | 來源 | 用途 |
|------|------|------|
| **context7** | claude-plugins-official | 查詢最新函式庫文件 |
| **claude-mem** | thedotmack | 跨 Session 持久記憶 |
| **cartographer** | kingbootoshi | 程式碼庫地圖產生 |
| **review-loop** | hamelsmu | 獨立程式碼審查迴圈 |
| **claude-hud** | jarrodwatts | 狀態列 HUD 顯示 |
| **telegram** | claude-plugins-official | Telegram 整合 |
| **github** | claude-plugins-official | GitHub 整合 |
| **typescript-lsp** | claude-plugins-official | TypeScript 語言伺服器 |
| **pyright-lsp** | claude-plugins-official | Python 型別檢查 |
| **playwright** | claude-plugins-official | 瀏覽器自動化 |
| **chrome-devtools-mcp** | claude-plugins-official | Chrome DevTools 存取 |

### Hook（自動觸發動作）

**寫入/編輯後（PostToolUse Write|Edit）：**
1. **Python 格式化：** `ruff format` + `ruff check --fix`（15 秒逾時）
2. **JS/TS 格式化：** `npx prettier --write`（15 秒逾時）

### 狀態列
- 使用 **claude-hud** 外掛（bun 執行環境）

### Worktree 設定
- 符號連結（Symlink）：`node_modules`、`.cache`

### MCP 伺服器
- 全域設定（`~/.claude/mcp_servers.json`）：空 — 全部透過外掛載入
- 專案層級 MCP：自動啟用（`enableAllProjectMcpServers: true`）

### 專案層級設定
- 27 個以上的專案目錄追蹤在 `~/.claude/projects/` 之下
- 大量使用 `C--DEX-data-Claude-Code-DEV-*` 變體（依日期分 Session）
- SOP 管線（S0-S7）設定在各專案的 CLAUDE.md 中
- 語言政策：繁體中文對話、英文程式碼

### 相關筆記
- [[dexg16-ai-coding-tools]]
- [[claude-session-manager]]

## 筆記
