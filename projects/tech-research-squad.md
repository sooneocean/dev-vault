---
title: "Tech Research Squad"
type: project
tags: [prompt-engineering, context-engineering, harness-engineering, compound-engineering]
created: "2026-03-29"
updated: "2026-03-30"
last_sprint: "Sprint 4 — Prompt Engineering"
status: active
maturity: growing
domain: ai-engineering
summary: "四大工程學科的迭代研究與反思框架 — Prompt / Context / Harness / Compound Engineering"
goal: "透過持續 onboarding 與反思迭代，建立可複利的 AI 工程知識體系"
deadline: ""
related: ["[[compound-engineering-plugin]]", "[[claude-code-configuration]]", "[[claude-code-dev-tools]]", "[[research-update-mode]]", "[[context-engineering-hygiene]]"]
---

# Tech Research Squad

## Goal

透過持續 onboarding 與反思迭代，深入研究四大 AI 工程學科，建立可複利的知識體系。

## 四大學科

| 學科 | 核心問題 | 研究筆記 |
|------|---------|---------|
| Prompt Engineering | 如何寫出讓 LLM 精準執行的指令？ | [[prompt-engineering-research]] |
| Context Engineering | 如何在有限 context window 中最大化有效資訊？ | [[context-engineering-research]] |
| Harness Engineering | 如何設計 agent 的工具鏈、hook、plugin 架構？ | [[harness-engineering-research]] |
| Compound Engineering | 如何讓每次工作累積為下次的加速器？ | [[compound-engineering-research]] |

## 反思框架（每次迭代填寫）

```
### Sprint N — YYYY-MM-DD

**做了什麼：**
**學到什麼：**
**哪裡卡住：**
**下次要試：**
**知識複利：** （這次的成果如何讓未來更快？）
```

## Progress

| Date | Update |
|------|--------|
| 2026-03-29 | 專案建立；安裝 Compound Engineering Plugin；建立四大學科研究筆記 |
| 2026-03-29 | Sprint 1: Harness 全貌盤點完成 — 14 plugins, 47 agents, 41 skills |
| 2026-03-29 | Sprint 2: obsidian-agent 底層效率改進 — session-stop wrapper + sync hook + bridge commands |
| 2026-03-29 | Sprint 3: Context Engineering 深入研究 + 落地 — CLAUDE.md 瘦身 78→22 行、compaction 策略、memory 強化、plugin baseline |
| 2026-03-30 | Sprint 4: Prompt Engineering 深入研究 — Claude 4.x 世代轉變、XML 結構化、CoT/Few-shot、CLAUDE.md 指令最佳化、Agent 工作流提示、Opus/Sonnet 差異、反模式整理 |

## TODO

- [x] 完成四大學科的初始研究筆記
- [x] 第一輪反思迭代（Harness Engineering）
- [x] 用 `/ce:brainstorm` 或 `/ce:plan` 跑一個真實任務
- [x] 深入研究 Prompt Engineering — Claude 4.x 提示技巧、CLAUDE.md 最佳化、Agent 工作流提示
- [x] 深入研究 Context Engineering — compaction 與 memory 策略
- [ ] 建立跨學科關聯圖

## Notes

- 這個專案是長期運行的，沒有固定 deadline
- 每次 onboard 新工具或技術時，回到這裡更新對應學科的筆記
- 反思框架是核心 — 每次迭代都要填寫，這是知識複利的關鍵
