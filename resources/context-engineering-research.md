---
title: "Context Engineering 研究"
type: resource
tags: [research, context-engineering, llm, context-window, memory]
created: "2026-03-29"
updated: "2026-03-29"
status: active
summary: "Context Engineering — 在有限 context window 中最大化有效資訊的策略"
source: ""
related: ["[[tech-research-squad]]", "[[prompt-engineering-research]]", "[[harness-engineering-research]]", "[[compound-engineering-research]]"]
---

# Context Engineering 研究

## 核心問題

如何在有限的 context window 中最大化有效資訊，讓 LLM 做出最好的決策？

## 關鍵概念

| 概念 | 說明 |
|------|------|
| Context window | 模型一次能處理的 token 上限（Opus 4.6: 1M） |
| Context pollution | 無關資訊稀釋了有效資訊的注意力 |
| Compaction | 壓縮對話歷史，保留關鍵資訊 |
| Subagent isolation | 用子代理隔離大範圍探索，避免污染主 context |
| CLAUDE.md | 每次對話自動載入的持久化 context |
| Memory system | 跨 session 的持久化記憶 |

## 已知策略

- Subagent 隔離大範圍搜索
- /compact 在自然斷點時壓縮
- CLAUDE.md 放最重要的持久指令
- Memory 跨 session 保留非顯而易見的知識
- 避免在主 context 中 Read 大檔案

## 迭代紀錄

<!-- 每次有新發現時在這裡追加 -->

## 開放問題

- 1M context 的實際有效利用率是多少？
- Compaction 時哪些資訊最容易丟失？
- 怎樣的 CLAUDE.md 結構最有效？

## Related

- [[tech-research-squad]]
- [[prompt-engineering-research]]
