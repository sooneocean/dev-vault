---
title: "CSM 關鍵設計決策"
type: resource
tags: [architecture]
created: "2026-03-28"
updated: "2026-03-29"
status: active
subtype: reference
maturity: mature
domain: project-specific
summary: "架構決策紀錄：不用互動式子程序、短命程序、stream-json 解析"
source: ""
related: ["[[csm-architecture]]", "[[csm-feature-roadmap]]", "[[pretext-csm-tui-layout]]"]
relation_map: "claude-session-manager:documents, csm-architecture:extends"
---

# CSM 關鍵設計決策

## 重點

### ADR-1：不使用互動式子程序
- **決策：** 使用 `claude -p`（列印模式）取代互動式子程序。
- **背景：** Claude CLI 偵測 `isatty()` 後，當 stdout 被管道導引時會抑制輸出。
- **影響：** 每個指令都啟動新的短命程序；透過 `--resume SESSION_ID` 恢復對話。
- **證據：** [[Wave 0 validation|docs/wave0_cli_findings.md]]

### ADR-2：Stream-JSON 解析
- **決策：** 解析 `--output-format stream-json` 結構化輸出。
- **背景：** 產生型別化的 JSON 事件（ResultEvent、AssistantEvent、InitEvent），而非非結構化文字。
- **影響：** 費用擷取可靠、SOP 階段偵測精準、不需靠正規表達式猜測。

### ADR-3：自動壓縮門檻
- **決策：** Token 使用量超過 50K 時自動發送 `/compact`。
- **背景：** 防止長時間 Session 的 Context Window 溢出。
- **影響：** Session 無需人工介入即可保持健康。

### ADR-4：失敗重試一次
- **決策：** Claude 呼叫失敗時重試一次，仍失敗才標記 Session 為 DEAD。
- **背景：** 暫態 CLI 錯誤時有發生，一次重試能攔截大部分情況。
- **影響：** 提升 Session 穩定性。

### ADR-5：SDD 框架開發
- **決策：** 完全由 Claude Code 使用 SDD S0-S7 管線建構。
- **背景：** TDD（先寫 150 項測試）、對抗式審查（R1-R3）、規格收斂（5 輪）。
- **影響：** 高測試覆蓋率、設計決策有完整文件佐證。

## 筆記

## 相關筆記

- [[claude-session-manager]]
- [[csm-architecture]]
