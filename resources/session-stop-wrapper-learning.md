---
title: "Session-Stop Wrapper Learning"
type: resource
tags: [hooks, harness-engineering, reference, knowledge-management]
created: "2026-03-29"
updated: "2026-04-03"
status: active
subtype: learning
maturity: mature
domain: ai-engineering
summary: "Wrapper script 繞過 CLI 限制，從 Stop hook stdin 擷取 last_assistant_message 寫入 journal"
source: "docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md"
related: ["[[tech-research-squad]]", "[[harness-engineering-research]]", "[[compound-engineering-plugin]]", "[[claude-code-configuration]]", "[[cli-update-fields-flag]]"]
relation_map: "harness-engineering-research:implements"
---

# Session-Stop Wrapper Learning

## Key Points

- `obsidian-agent sessionStop()` 只讀 `stop_reason`，忽略 `last_assistant_message`
- 解法：bash wrapper script 直接讀 stdin JSON，用 `jq` 提取摘要
- 三層 fallback：`last_assistant_message` → `git diff --stat` → 基本時間戳
- `obsidian-agent patch --heading --append` 可靠追加到指定 section
- Windows Git Bash + jq stdin 管道穩定可用

## Pattern: Wrapper Over CLI Modification

當 CLI 功能不足但不想改核心時：
1. 用 wrapper script 攔截 stdin/stdout
2. 在 wrapper 中做額外處理
3. 最後呼叫原始 CLI 命令
4. 驗證成功後再考慮 upstream PR

這個模式可複製到其他 hook 自動化場景。

## Notes

- 完整技術細節見 [compound learning](docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md)
- 實作計畫見 [efficiency plan](docs/plans/2026-03-29-002-feat-obsidian-agent-efficiency-plan.md)

## Related

- [[tech-research-squad]] — Sprint 2 成果
- [[harness-engineering-research]] — Hook 自動化實踐
- [[claude-code-configuration]] — settings.json Stop hook 配置
