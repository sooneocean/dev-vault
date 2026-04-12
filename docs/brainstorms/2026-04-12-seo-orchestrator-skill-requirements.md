---
date: 2026-04-12
topic: seo-orchestrator-skill
---

# SEO Orchestrator Skill — 從零重新設計

## Problem Frame

現有的 site-optimizer 是一個 CLI 包裝器 + 散落的批次腳本集合。它能用，但存在根本性問題：

1. **體驗碎片化** — 用戶必須知道該用哪個 phase、哪個腳本、什麼參數。這是工具思維，不是顧問思維。
2. **能力散落** — meta-tags 和 schema-markup 的邏輯存在於獨立的 phase 腳本中（`phase4-complete-seo-batch-generator.js` 等），但未整合進框架。框架宣稱支持但實際拋出 "coming soon" 錯誤。
3. **無全局視角** — 沒有「你的網站 SEO 整體狀況如何」的能力，只有逐項優化的工具。
4. **無數據驅動決策** — 不知道哪些頁面需要優先優化，不參考實際流量數據。

**目標用戶：** 擁有 WordPress.com 網站的內容創作者（主要是 yololab.net），想要持續提升 SEO 表現但不想成為 SEO 專家。

**核心願景：** 用戶只需說「幫我看看 SEO」，Skill 就像一個資深 SEO 顧問一樣——自動診斷、排定優先級、執行優化、報告結果。

## User Flow

```
用戶: 「幫我優化 SEO」或「/seo」
        │
        ▼
┌─────────────────────────┐
│  SEO Orchestrator Skill │
│  ┌───────────────────┐  │
│  │ 1. Health Check   │  │  ← 自動：抓取網站數據、跑全維度診斷
│  │    (自動執行)      │  │
│  └────────┬──────────┘  │
│           ▼              │
│  ┌───────────────────┐  │
│  │ 2. Priority Matrix│  │  ← 自動：根據影響力排序優化建議
│  │    (自動生成)      │  │     顯示：分數、建議、預估效果
│  └────────┬──────────┘  │
│           ▼              │
│  ┌───────────────────┐  │
│  │ 3. 用戶確認       │  │  ← 關鍵決策點：用戶選擇執行哪些
│  │   「執行全部？」   │  │     或調整優先級
│  └────────┬──────────┘  │
│           ▼              │
│  ┌───────────────────┐  │
│  │ 4. Execute        │  │  ← 自動：按優先級批次執行
│  │   (modules 並行)   │  │     每個 module 獨立、可回滾
│  └────────┬──────────┘  │
│           ▼              │
│  ┌───────────────────┐  │
│  │ 5. Report + Next  │  │  ← 自動：結果報告 + 下次建議
│  │    (自動生成)      │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

## Requirements

**Orchestrator 核心**

- R1. 單一入口 `/seo` 觸發 Skill，接受自然語言指令（如「優化圖片 ALT」「做個全面健檢」「上次的報告呢」）
- R2. 智能自動駕駛模式：Skill 自主判斷診斷範圍、優先級、執行順序，僅在不可逆操作（apply / rollback）前徵求用戶確認
- R3. 全站 SEO 健康分數系統（0-100），涵蓋所有優化維度，每次執行後更新
- R4. Priority Matrix：根據預估 SEO 影響力（搜尋曝光提升潛力）自動排序優化項目

**優化模組（Modules）**

- R5. Image ALT 優化 — 提取現有 `image-alt-text-optimizer.js` 核心邏輯，重構為 module 介面
- R6. Meta Tags 優化 — 提取現有 phase 腳本中的 meta title/description 生成邏輯，統一為 module
- R7. Schema Markup 注入 — 提取現有 phase 腳本中的 JSON-LD 生成邏輯，統一為 module
- R8. Internal Links 優化 — 提取現有 `internal-linker-v2.js` 核心邏輯，重構為 module 介面
- R9. Content Quality 分析 — 新建 module：內容品質審計（關鍵字密度、可讀性分數、薄弱內容偵測、重複內容識別）
- R10. Core Web Vitals 監控 — 新建 module：透過 PageSpeed Insights API 或 CrUX 數據追蹤 LCP/FID/CLS
- R11. 競爭對手分析 — 新建 module：指定競爭對手 URL，對比 SEO 策略差異
- R12. 反向連結監控 — 新建 module：追蹤外部反向連結變化（需外部 API 或 WebSearch 實現）

**Module 統一介面**

- R13. 每個 module 必須實現統一介面：`audit()` → `plan()` → `execute()` → `verify()` → `report()`
- R14. 每個 module 獨立可回滾，備份在執行前自動建立
- R15. Module 之間無硬依賴，orchestrator 決定執行順序和並行策略

**數據與狀態**

- R16. 持久化健康分數歷史，支持趨勢追蹤（「上個月到現在改善了多少？」）
- R17. 執行歷史記錄，支持查詢（「上次優化了什麼？」「哪些文章被修改過？」）
- R18. 整合 wpcom-mcp 作為 WordPress API 通道，取代直接 REST API 呼叫（當可用時）

**報告與洞察**

- R19. 每次執行後生成結構化報告：改動摘要、前後對比、預估影響
- R20. 支持自然語言查詢歷史數據（「圖片 ALT 覆蓋率現在多少？」「哪些文章 SEO 分數最低？」）

## Success Criteria

- 用戶說「/seo」後，在 2 分鐘內看到全站健康分數和 top 5 優化建議
- 任何優化操作都能在一次對話中從診斷到執行完成
- 新增一個優化 module 只需：(1) 實現統一介面 (2) 在 orchestrator 註冊
- 錯誤操作可在一個指令內完全回滾

## Scope Boundaries

- **不做** WordPress.org (self-hosted) 支持 — 僅 WordPress.com REST API / wpcom-mcp
- **不做** 付費 SEO 工具 API 整合（Ahrefs、SEMrush 等）— 使用 WebSearch 作為免費替代
- **不做** 自動發佈/排程 — Skill 優化現有內容，不創建新內容
- **不做** 多語言內容生成 — 生成的 ALT/meta 使用網站設定語言（yololab = zh_TW）
- **不做** 即時 GSC 數據整合 — GSC API 需另外授權，列為未來增強（R10 用 PageSpeed Insights 替代）

## Health Score Weighting

按 SEO 影響力加權（已確認）：

| 維度 | 權重 | 理由 |
|------|------|------|
| Meta Tags | 30% | 直接影響 SERP 顯示和 CTR |
| Image ALT | 20% | 圖片搜尋流量 + 無障礙合規 |
| Schema Markup | 15% | Rich snippets 和結構化數據 |
| Internal Links | 15% | 頁面權重傳遞和爬蟲效率 |
| Content Quality | 10% | 內容深度和相關性 |
| Core Web Vitals | 10% | 技術性能和用戶體驗 |

## Key Decisions

- **單一 Orchestrator Skill 而非 Skill 家族**：用戶體驗一致性 > 架構簡潔性。Skill prompt 長度風險透過 module 化緩解——orchestrator 只做決策和調度，重活由 module 腳本執行。
- **智能自動駕駛模式**：減少用戶決策疲勞。只在不可逆操作前暫停確認。
- **提取現有邏輯而非重寫**：`image-alt-text-optimizer.js`（1,258 行）和 `internal-linker-v2.js`（519 行）已經過生產驗證，重構為 module 介面而非丟棄重寫。
- **wpcom-mcp 優先**：當 MCP 可用時使用 wpcom-mcp 通道，fallback 到直接 REST API。這樣 Skill 在 Claude Code 環境中獲得最佳整合。

## Dependencies / Assumptions

- wpcom-mcp server 持續可用且支持文章/媒體的 CRUD 操作
- `WPCOM_TOKEN` 和 `ANTHROPIC_API_KEY` 環境變數已設定
- 現有腳本（`image-alt-text-optimizer.js`、`internal-linker-v2.js`、`phase4-complete-seo-batch-generator.js`）的核心邏輯可提取為獨立函數
- PageSpeed Insights API 免費額度足夠日常使用（每日 25,000 次查詢）
- 認證統一：直接 REST API 呼叫使用 `WPCOM_TOKEN`（Bearer token），wpcom-mcp 通道使用 MCP server 內建認證（不需環境變數）。現有腳本中的 `WP_BEARER_TOKEN`、`WP_APP_USER`/`WP_APP_PASS` 將統一為 `WPCOM_TOKEN`

## Outstanding Questions

### Resolve Before Planning

（全部已解決）

### Deferred to Planning

- [Affects R5-R8][Technical] 現有腳本重構為 module 介面的最佳策略：包裝 vs 重寫核心函數？需要評估現有程式碼的可提取性
- [Affects R10][Needs research] PageSpeed Insights API vs CrUX API：哪個更適合作為 Core Web Vitals 數據源？需研究 API 限制和數據延遲
- [Affects R11][Needs research] 免費競爭對手分析的可行方案：WebSearch scraping 的可靠性和法律風險？
- [Affects R12][Needs research] 免費反向連結監控方案：是否有可靠的免費 API 或需要依賴 WebSearch？
- [Affects R13][Technical] Module 統一介面的具體 contract（TypeScript interface / JSDoc）設計
- [Affects R16-R17][Technical] 狀態持久化方案：JSON 文件 vs SQLite vs vault 筆記？

## Next Steps

→ `/ce:plan` for structured implementation planning
