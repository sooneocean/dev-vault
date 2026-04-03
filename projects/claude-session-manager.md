---
title: "Claude Session Manager"
type: project
tags: [claude-code, python, project, active]
created: "2026-03-28"
updated: "2026-04-03"
status: active
maturity: growing
domain: project-specific
summary: true
goal: "Enable multi-session Claude Code management from a single TUI dashboard with real-time streaming, cost tracking, SOP detection, auto-compaction at 50K tokens, and persistent session state"
deadline: ""
related: ["[[claude-code-dev-tools]]", "[[dexg16-ai-coding-tools]]", "[[claude-code-configuration]]", "[[session-stop-wrapper-learning]]", "[[pretext-csm-tui-layout]]", "[[tech-research-squad]]"]
relation_map: "csm-architecture:documents, csm-feature-roadmap:documents"
---

# Claude Session Manager

## 目標

提供單一終端儀表板，同時管理 10 個以上的 Claude Code Session — 即時串流輸出、費用追蹤、SOP 階段偵測、Session 持久化、自動壓縮（auto-compact）。

## 進度

| 日期 | 更新 |
|------|------|
| 2026-03-15 | v0.1.0 — 首次發布 |
| 2026-03-15 | v0.3.0 — 即時串流輸出 |
| 2026-03-15 | v0.7.0 — psutil 系統監控、重試機制 |
| 2026-03-15 | v0.9.0 — 50K token 自動壓縮 |
| 2026-03-28 | v0.53.0 — 目前穩定版，150 項測試通過 |

## 待辦

- [ ] 評估 v2 重構方案（見 [[csm-feature-roadmap]]）
- [ ] 合併 claude-session-manager 與 claude-session-manager-new 兩套程式碼
- [ ] 發布至 PyPI

## 筆記

### 技術堆疊
- **執行環境：** Python 3.10+（asyncio、union types）
- **TUI 框架：** Textual >=0.80
- **測試：** pytest + pytest-asyncio（150 項測試）
- **可選：** psutil（系統監控）、textual-serve（瀏覽器模式）

### 核心功能
- 透過 `--include-partial-messages` 即時串流輸出
- 從 claude CLI 結構化 JSON 輸出中擷取費用資料
- SOP 階段（S0-S7）偵測，依據輸出模式自動識別
- 50K token（輸入+輸出合計）觸發自動壓縮
- Session 狀態持久化至 `~/.csm/sessions.json`
- 支援 Session 複製、筆記、標籤、廣播指令
- 透過 `textual serve` 啟用瀏覽器模式
- 透過 `~/.csm/config.json` 自訂設定

### 快捷鍵
N=新增, Enter=發送指令, X=停止, D=刪除, R=重啟, E=匯出, C=複製, F=搜尋, A=筆記, T=標籤, I=統計, B=廣播, Q=離開

### 相關筆記
- [[csm-architecture]]
- [[csm-key-design-decisions]]
- [[csm-feature-roadmap]]
- [[claude-code-dev-tools]]
- [[dev-vault-status]] — 同屬 Claude Code 生態系的知識管理工具
- [[tech-research-squad]] — 研究 context management 和工程化基礎
