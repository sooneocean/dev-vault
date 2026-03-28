---
title: "CSM 架構"
type: resource
tags: [architecture, python, textual]
created: "2026-03-28"
updated: "2026-03-28"
status: active
summary: "Claude Session Manager 技術架構 — 程序模型、串流、持久化"
source: ""
related: ["[[csm-key-design-decisions]]", "[[csm-feature-roadmap]]", "[[claude-code-configuration]]"]
---

# CSM 架構

## 重點

- **程序模型（Process Model）：** 短命程序 — 每次 `send_command()` 都會啟動 `claude -p --output-format stream-json --verbose --include-partial-messages "prompt"`，不維護長期運行的子程序。
- **恢復對話（Resume）：** 下一個指令使用 `--resume SESSION_ID` 延續對話。
- **串流（Streaming）：** 逐行讀取 stdout，透過 `OutputParser` 即時解析 JSON 事件。
- **持久化（Persistence）：** 離開時將 Session 狀態儲存到 `~/.csm/sessions.json`，下次啟動自動還原。
- **自動壓縮（Auto-Compact）：** Token 使用量超過 50K 門檻時自動發送 `/compact`。
- **失敗重試（Retry）：** Claude 呼叫失敗時重試一次，仍失敗才標記為 DEAD。

## 筆記

### 模組結構

```
src/csm/
├── app.py                  # Textual App — 佈局、快捷鍵、更新迴圈
├── core/
│   ├── session_manager.py  # 啟動/停止/重啟、自動壓縮
│   ├── output_parser.py    # stream-json → 型別化 dataclass
│   ├── command_dispatcher.py # 每個 Session 的 FIFO 佇列
│   ├── persistence.py      # 儲存/載入 ~/.csm/sessions.json
│   ├── config.py           # 設定管理
│   └── templates.py        # 模板系統
├── models/
│   ├── session.py          # SessionState、SessionConfig、SessionStatus
│   └── cost.py             # CostAggregator、CostSummary
├── widgets/
│   ├── session_list.py     # DataTable，支援篩選/排序
│   ├── detail_panel.py     # RichLog，漸進式串流顯示
│   ├── stats_panel.py      # 儀表板統計
│   └── modals/             # 新增 Session、確認停止、說明等對話框
├── utils/
│   ├── ring_buffer.py      # 固定容量雙端佇列（1000 行）
│   └── ansi.py             # 移除 ANSI 跳脫碼 + CR
└── api/
    └── server.py           # 可選的 API 伺服器
```

### 關鍵常數
| 常數 | 值 |
|------|------|
| SESSION_LIMIT（Session 上限） | 20 |
| AUTO_COMPACT_TOKEN_THRESHOLD（自動壓縮門檻） | 50,000 |
| QUEUE_MAX_SIZE（佇列上限） | 50 |
| RingBuffer 容量 | 1,000 行 |
| 程序逾時 | 600 秒 |

### 相關筆記
- [[claude-session-manager]]
- [[csm-key-design-decisions]]
