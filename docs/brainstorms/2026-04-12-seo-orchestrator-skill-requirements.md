---
date: 2026-04-12
topic: seo-orchestrator-skill
---

# SEO Orchestrator Skill — 從零重新設計

## Problem Frame

現有的 site-optimizer 是一個 CLI 包裝器 + 散落的批次腳本集合。它能用，但存在根本性問題：

1. **體驗碎片化** — 用戶必須知道該用哪個 phase、哪個腳本、什麼參數。這是工具思維，不是顧問思維。
2. **能力散落** — meta-tags 和 schema-markup 的邏輯已存在於 `phase4-complete-seo-batch-generator.js` 和 `phase4-apply-seo-to-wordpress.js` 中，但未整合進框架。框架宣稱支持但實際拋出 "coming soon" 錯誤。
3. **無全局視角** — 沒有「你的網站 SEO 整體狀況如何」的能力，只有逐項優化的工具。
4. **腳本膨脹** — `scripts/` 中累積了 ~47 個 SEO 相關腳本（含多版本和分批處理），無統一入口或廢棄計畫。

**目標用戶：** 擁有 WordPress.com 網站的內容創作者（主要是 yololab.net），想要持續提升 SEO 表現但不想成為 SEO 專家。

**核心願景：** 用戶只需說「幫我看看 SEO」，Skill 就像一個資深 SEO 顧問一樣——自動診斷、排定優先級、執行優化、報告結果。

## Delivery Phases

```
Phase 1 (MVP)                          Phase 2 (擴展)
─────────────────────────────          ─────────────────────────────
整合現有 4 個模組 (R5-R8)              新增模組 (R9-R12)
/seo 入口 + 顧問式對話                 Health Score 數值系統
SEO 摘要報告                           持久化歷史 + 趨勢追蹤
每模組獨立備份/回滾                     自動化排程
腳本整合 + 舊腳本廢棄計畫               GSC 整合（如可行）
```

## Requirements

### Phase 1 — MVP（核心交付）

**Skill 入口**

- R1. 單一入口 `/seo` 觸發 Skill，接受自然語言指令（如「優化圖片 ALT」「做個全面健檢」「幫我看看 SEO」）
- R2. 對話式驅動：Skill 分析網站狀態後，以顧問角色建議優化方向和優先級。在批次寫入操作前徵求用戶確認，包含預估影響範圍（篇數、類型）

**優化模組（已有實現的提取）**

- R5. Image ALT 優化 — 提取 `image-alt-text-optimizer.js` 核心邏輯，包裝為可被 orchestrator 調用的模組
- R6. Meta Tags 優化 — 提取 `phase4-complete-seo-batch-generator.js` + `phase4-apply-seo-to-wordpress.js` 中的 meta title/description 生成和應用邏輯
- R7. Schema Markup 注入 — 提取上述 phase4 腳本中的 JSON-LD 生成和注入邏輯
- R8. Internal Links 優化 — 提取 `internal-linker-v2.js` 核心邏輯，包裝為模組

**共享工具庫（取代統一介面）**

- R13. 提供共享工具庫（shared utilities）而非強制統一介面：共用 API fetch（含速率限制、重試）、備份/回滾邏輯、報告格式化器。每個模組保持自己的自然工作流結構
- R14. 每個模組獨立可回滾，備份在執行前自動建立。需為目前缺少回滾的模組（meta-tags、schema、internal-links）補充備份邏輯
- R15. 模組之間無硬依賴，orchestrator 決定執行順序

**報告**

- R19. 每次執行後生成結構化摘要：改動清單、受影響文章數、失敗項目。以對話形式呈現，非獨立報告文件

**腳本整合**

- R21. 制定舊腳本廢棄計畫：識別 `scripts/` 中可被新模組取代的腳本，標記為 deprecated，在 Phase 1 完成後清理

### Phase 2 — 擴展（驗證可行性後再納入）

以下需求需先驗證可行性，不阻擋 Phase 1 交付：

- R3. 全站 SEO 健康分數系統（0-100），基於已實現模組的覆蓋率數據。僅在有足夠數據來源時才有意義
- R4. Priority Matrix：根據實際覆蓋率缺口（而非預設權重）排序優化建議
- R9. Content Quality 分析 — 內容品質審計（關鍵字密度、可讀性、薄弱內容偵測）
- R10. Core Web Vitals 監控 — 透過 PageSpeed Insights API 追蹤 LCP/FID/CLS
- R11. 競爭對手分析 — 指定競爭對手 URL，對比 SEO 策略差異（需先驗證免費方案可行性）
- R12. 反向連結監控 — 追蹤外部反向連結變化（需先驗證免費 API 或 WebSearch 方案）
- R16. 持久化健康分數歷史，支持趨勢追蹤
- R17. 執行歷史記錄
- R20. 自然語言查詢歷史數據

## Success Criteria

**Phase 1:**
- 用戶說「/seo」後，Skill 能在對話中分析現有模組覆蓋率並建議下一步行動
- 任何優化操作（image-alt、meta-tags、schema、internal-links）都能在一次對話中從診斷到執行完成
- `meta-tags` 和 `schema-markup` 不再拋出 "coming soon" 錯誤
- 每個模組的寫入操作都可回滾
- 新增模組只需：(1) 寫腳本 (2) 在 orchestrator 中註冊路由

**Phase 2:**
- 健康分數基於實際數據，非預設權重
- 能追蹤 SEO 指標變化趨勢

## Scope Boundaries

- **不做** WordPress.org (self-hosted) 支持 — 僅 WordPress.com REST API / wpcom-mcp
- **不做** 付費 SEO 工具 API 整合（Ahrefs、SEMrush 等）
- **不做** 自動發佈/排程 — Skill 優化現有內容，不創建新內容
- **不做** 多語言內容生成 — 生成的 ALT/meta 使用網站設定語言（yololab = zh_TW）
- **不做** 即時 GSC 數據整合 — GSC API 需另外授權，列為 Phase 2+ 增強
- **Phase 1 不做** 數值化健康分數 — 先以文字摘要呈現覆蓋率，Phase 2 再加入計分系統

## Key Decisions

- **MVP 分層交付**：Phase 1 專注整合已有的 4 個模組 + `/seo` 入口，解決碎片化和 "coming soon" 兩個核心痛點。Phase 2 加入新模組和智能化功能。先交付再迭代。
- **共享工具庫取代統一介面**：不強制所有模組實現 `audit()→plan()→execute()→verify()→report()` 五步介面。改為提供共用 utilities（API fetch、備份、報告），每個模組保持自己的自然工作流。避免為了架構一致性而重寫已驗證的 1,258 行 image-alt 腳本。
- **對話式而非全自動駕駛**：Phase 1 的 orchestrator 是對話式顧問，分析後建議並等待確認。不做「自主判斷一切只在最後問一次」的 autopilot——避免靜默觸發昂貴操作（2,728 篇 × Claude Vision = $3-5 + 8-10 小時）。
- **提取現有邏輯而非重寫**：`image-alt-text-optimizer.js`（1,258 行）和 `internal-linker-v2.js`（519 行）已經過生產驗證，包裝為模組而非丟棄重寫。
- **API 通道策略留給 planning**：wpcom-mcp 的 per-write 確認協議與批次操作存在根本衝突，需在 planning 階段研究最佳方案（讀用 MCP / 寫用 REST、全用 REST、或其他方案）。

## Dependencies / Assumptions

- `WPCOM_TOKEN` 和 `ANTHROPIC_API_KEY` 環境變數已設定
- 現有腳本（`image-alt-text-optimizer.js`、`internal-linker-v2.js`、`phase4-complete-seo-batch-generator.js`、`phase4-apply-seo-to-wordpress.js`）的核心邏輯可提取為獨立函數
- 認證統一：直接 REST API 呼叫使用 `WPCOM_TOKEN`（Bearer token）。現有腳本中的 `WP_BEARER_TOKEN`、`WP_APP_USER`/`WP_APP_PASS` 將統一為 `WPCOM_TOKEN`
- yololab.net 的 WordPress.com 方案支持所需的 post meta 寫入（Yoast SEO 欄位或等效方案）— 需在 planning 階段驗證

## Outstanding Questions

### Resolve Before Planning

（全部已解決）

### Deferred to Planning

- [Affects R5-R8][Technical] 現有腳本包裝策略：每個模組的入口函數應暴露什麼 API？需評估現有程式碼的封裝邊界
- [Affects R6-R7][Technical] `phase4-apply-seo-to-wordpress.js` 使用 Yoast SEO meta fields（`_yoast_wpseo_title` 等）。需驗證 yololab.net 是否支持，並確認 wpcom-mcp 是否能寫入這些欄位
- [Affects R2/R18][Technical] wpcom-mcp per-write 確認協議與批次操作的衝突：研究最佳 API 通道策略
- [Affects R14][Technical] 為 meta-tags、schema、internal-links 模組設計回滾機制（目前只有 image-alt 有備份邏輯）
- [Affects R21][Technical] 盤點 `scripts/` 中 ~47 個 SEO 腳本，制定保留/廢棄/整合清單
- [Affects R13][Technical] 共享工具庫的具體 API 設計（fetch wrapper、backup helper、report formatter）

### Phase 2 Research（不阻擋 Phase 1）

- [Affects R10][Needs research] PageSpeed Insights API vs CrUX API：適合度、API 限制、數據延遲
- [Affects R11][Needs research] 免費競爭對手分析方案的可行性和法律風險
- [Affects R12][Needs research] 免費反向連結監控方案
- [Affects R3][Needs research] 健康分數的權重應基於實際 GSC 數據還是啟發式規則？Phase 2 需要 feedback loop

## Next Steps

→ `/ce:plan` for structured implementation planning
