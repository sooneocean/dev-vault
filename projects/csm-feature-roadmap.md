---
title: "CSM 功能路線圖"
type: project
tags: [planning, project, active]
created: "2026-03-28"
updated: "2026-04-03"
status: active
maturity: growing
domain: project-specific
summary: "CSM 的版本演進與未來功能規劃"
goal: "Define version roadmap from v0.53 (current stable) through v2 refactor: TUI optimization, async test fixes, plugin system, cross-machine sync, and PyPI release"
deadline: ""
related: ["[[csm-architecture]]", "[[csm-key-design-decisions]]", "[[dexg16-git-and-github]]", "[[pretext-csm-tui-layout]]", "[[Unit4-Gospel-Recruitment-Plan]]"]
relation_map: "claude-session-manager:documents"
---

# CSM 功能路線圖

## 目標

追蹤 [[claude-session-manager]] 的功能演進，規劃未來開發方向。

## 版本歷程

| 日期 | 版本 | 重點更新 |
|------|------|----------|
| 2026-03-15 | v0.1.0 | 首次發布：基本 Session 啟動/停止 |
| 2026-03-15 | v0.2.0 | 品質重構 + Session 持久化 |
| 2026-03-15 | v0.3.0 | 即時串流輸出 |
| 2026-03-15 | v0.4.0 | /iterate 技能，自動化迭代 |
| 2026-03-15 | v0.5.0 | Session 命名、README |
| 2026-03-15 | v0.6.0 | 說明畫面、廣播指令 |
| 2026-03-15 | v0.7.0 | psutil 系統監控、重試機制 |
| 2026-03-15 | v0.8.0 | 歡迎畫面、空白狀態引導 |
| 2026-03-15 | v0.9.0 | 50K token 自動壓縮 |
| 2026-03-28 | v0.53.0 | 目前穩定版（v0.9 後大量迭代） |

## 待辦

- [ ] v2 重構（見 `dev/specs/csm-v2-refactor/`）
- [ ] TUI 效能優化（見 `dev/specs/tui-optimization/`）
- [ ] 修復非同步測試回歸（見 `dev/specs/fix-async-test-regression/`）
- [ ] PyPI 打包與發布
- [ ] 外掛系統：自訂輸出解析器
- [ ] 跨機器 Session 同步

## 筆記
