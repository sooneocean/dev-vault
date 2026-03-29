---
title: "Prompt Engineering 研究"
type: resource
tags: [prompt-engineering, llm]
created: "2026-03-29"
updated: "2026-03-30"
status: active
subtype: research
maturity: growing
domain: ai-engineering
summary: "Prompt Engineering 的技巧、模式、反模式與迭代心得"
source: ""
related: ["[[tech-research-squad]]", "[[context-engineering-research]]", "[[harness-engineering-research]]", "[[compound-engineering-research]]"]
relation_map: "tech-research-squad:extends"
---

# Prompt Engineering 研究

## 核心問題

如何寫出讓 LLM 精準、一致、可靠地執行任務的指令？

## 已知模式

| 模式 | 說明 | 適用場景 |
|------|------|---------|
| System prompt | 設定角色、規則、輸出格式 | 所有場景的基礎 |
| Few-shot | 提供範例讓 LLM 模仿 | 格式要求嚴格時 |
| Chain-of-thought | 要求逐步推理 | 複雜邏輯、數學 |
| Self-reflection | 讓 LLM 檢查自己的輸出 | 減少幻覺 |
| Structured output | 指定 JSON/XML 格式 | API 整合 |

## 反模式（踩過的坑）

-

## 迭代紀錄

<!-- 每次有新發現時在這裡追加 -->

## 開放問題

- 中文 vs 英文 prompt 的效果差異？
- CLAUDE.md 中的指令優先級如何運作？
- 長 system prompt vs 短 system prompt 的 trade-off？

## Related

- [[tech-research-squad]]
- [[context-engineering-research]]
