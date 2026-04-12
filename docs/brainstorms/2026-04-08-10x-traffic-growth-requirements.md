---
date: 2026-04-08
topic: 10x-traffic-growth
---

# YOLO LAB 10x 流量成長策略

## Problem Frame

YOLO LAB (yololab.net) 是繁體中文科技/媒體娛樂數據實驗室，目前月瀏覽量 34,270，70%+ 來自 Google 有機搜尋。網站擁有 2,728 篇文章但流量成長停滯。目標是 6-12 個月內達到 342,700+ 月瀏覽量（10x），僅使用技術 + AI 自動化手段，不投入人工編輯或付費推廣。

### 為什麼存量優化不夠

| 槓桿 | 預期提升 | 累計天花板 |
|-------|---------|-----------|
| 完成剩餘 1,800 篇 SEO 優化 | +50-80% | ~2x |
| 首頁重構 + 內鏈網路 | +30-50% | ~3x |
| 標籤架構整合 | +10-20% | ~3.5x |
| **存量極限** | | **~4x (130K)** |

結論：必須透過程式化內容擴張 + 多渠道分發突破存量天花板。

### 成長路徑

```
Month 1-2          Month 3-6           Month 6-12
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ Phase 1  │    │   Phase 2    │    │   Phase 3    │
│ 基底優化 │───>│  內容擴張    │───>│   放大器     │
│          │    │              │    │              │
│ 存量 SEO │    │ AI 生成      │    │ 多渠道分發   │
│ 首頁重構 │    │ 3,000-5,000  │    │ X/Threads    │
│ 內鏈網路 │    │ 新文章       │    │ LINE OA      │
│ 標籤架構 │    │ Topic Cluster│    │ RSS 自動化   │
│ 技術修復 │    │ 長尾關鍵字   │    │ 數據迭代     │
└──────────┘    └──────────────┘    └──────────────┘
  → 3-4x           → 6-8x              → 10x+
  (~100-130K)       (~200-270K)          (~340K+)
```

## Requirements

**Phase 1: 基底優化 (Month 1-2)**

*Technical & Infrastructure*
- R1. 修復技術問題：確認自訂域名綁定狀態（API 回報 `has_custom_domain: false`）和網站啟用狀態（`is_site_launched: false`），修復任何影響 SEO 的配置問題

*Content Optimization*
- R2. 完成剩餘 ~1,800 篇文章的 SEO 優化（Meta title/description、Schema markup、OG tags）。注意：現有 batch optimizer 僅驗證過 898 篇 2025 年文章，需先盤點剩餘文章並驗證工具相容性
- R3. 部署首頁重構：靜態首頁 + 5 個分類 Hub 區塊 + 首頁 Schema（WebSite + SearchAction + Organization）
- R4. 建立並部署內部連結網路：需開發連結注入腳本（現有 `proposed-links.json` 僅覆蓋 50 篇 Tier-1），目標消除 1,695 篇孤兒文章，每篇被至少 3 篇其他文章連結（1 pillar + 2 cluster peers），建立雙向內鏈
- R5. 執行標籤架構整合：5,000+ 標籤 → 150 個 super-tags，對應 5 大分類 Hub。舊標籤 URL 須執行 301 重定向至對應 super-tag 或最近似 Hub 頁面，避免產生大量 404

**Phase 2: 程式化內容擴張 (Month 3-6)**

*Data & Research*
- R6. 建立關鍵字研究自動化管線：識別 YOLO LAB 尚未覆蓋的長尾關鍵字空白區，目標發現 3,000-5,000 個可攻略的關鍵字。若免費工具無法取得搜尋量數據，備案為基於現有文章語料的 topic modeling + Google Suggest 趨勢分析

*Content Generation Pipeline*
- R7. 建立 AI 內容生成管線：根據關鍵字研究結果，自動生成符合 YOLO LAB 風格的文章，包含標題、正文、Meta tags、Schema markup、內鏈建議
- R8. 建立自動化品質閘門：每篇生成文章需通過以下檢查才能進入發布佇列：
  - 可讀性評分（字數、段落結構、標題層級）
  - 來源引用完整性（文中包含可連結外部來源）
  - SEO 評分（關鍵字密度、Meta 完整性、內鏈數量）
  - 重複內容檢測（與現有文章相似度 < 閾值）
  - 綜合品質分數 = 四項加權平均，≥ 70/100 才通過（權重與閾值由 Planning 確定）
- R9. 擴展 R4 的內鏈工具鏈至新生成文章：每個 Topic Cluster 有 1 篇 pillar page + 5-15 篇 cluster articles，使用同一套連結注入系統建立雙向內鏈
- R10. 自動化發布管線：通過品質閘門的文章自動排程發布到 WordPress，目標 30-50 篇/天（依 API rate limit 調整），含自動分類、標籤、特色圖片

**Phase 3: 多渠道分發放大 (Month 6-12)**

- R11. 自動化社群分發：每篇新文章自動生成平台適配的摘要並發布到 X (Twitter)、Threads、LINE OA。觸發機制（RSS 監聽或 WordPress webhook）為實作細節
- R12. 數據驅動迭代系統：自動收集 GSC + GA4 數據，識別高潛力文章進行內容升級，識別低表現文章進行合併或刪除

## Success Criteria

- SC1. Month 2 結束時月瀏覽量達 100,000+（~3x baseline）——依賴 R2-R5 全部完成
- SC2. Month 6 結束時月瀏覽量達 200,000+（~6x baseline）
- SC3. Month 12 結束時月瀏覽量達 342,700+（10x baseline）
- SC4. Google Search Console 無手動處罰或 Helpful Content 降級
- SC5. 新生成文章平均品質分數 ≥ 70/100（R8 品質閘門標準，四項加權平均）
- SC6. 內容發布管線達到平均 30+ 篇/天的穩定產出（日波動 ≤ ±20%）

## Phase Gate Criteria

- **Phase 1 → Phase 2：** R1-R5 全部完成 AND 月瀏覽量趨勢向上（不硬性要求 SC1 達標）
- **Phase 2 → Phase 3：** R10 穩定運行（30+ 篇/天持續 2 週）AND 無 SC4 違規
- **提前退出：** 任一 Phase 連續 2 個月未達預期目標的 50%，暫停並重新評估策略

## Scope Boundaries

- **不含**付費廣告（Google Ads、社群廣告）
- **不含**人工編輯審稿（全自動化流程）
- **不含**網站平台遷移（維持 WordPress.com Atomic）
- **不含**非繁體中文內容（暫不做多語言）
- **不含**影片內容製作（僅文字 + 圖片）
- Phase 2 的 AI 生成內容以「對使用者有用」為品質目標，透過 R8 自動化閘門把關（非人工審核 Helpful Content 政策合規性）

## Key Decisions

- **混合策略 (A+B)**：存量優化打底 + 程式化擴張衝量 + 多渠道放大。單靠存量 SEO 天花板約 4x，無法達到 10x
- **中品質 + 自動檢查**：AI 生成 + 自動化品質閘門（可讀性、來源引用、SEO 評分、重複檢測），通過即發布，30-50 篇/天。平衡速度與品質風險
- **6-12 個月時間框架**：Phase 1 打底 → Phase 2 擴張 → Phase 3 放大，分階段降低風險，每階段設 gate criteria
- **純技術 + AI 自動化**：不增加人手，全靠工具鏈和腳本，符合現有工作模式

## Dependencies / Assumptions

- Google Search Console 和 GA4 已正確配置且有歷史數據
- WordPress REST API 可正常批量操作文章（已驗證）
- Anthropic API 配額足夠支撐 3,000-5,000 篇內容生成（預估成本 $200-1,000，依模型選擇而定：Haiku ~$50、Sonnet ~$200、Opus ~$1,000）
- YOLO LAB 現有文章品質可作為風格訓練基礎
- 現有 batch optimizer 需擴展至 2023-2024 年文章（尚未驗證相容性）
- R4 連結注入腳本需從頭開發（現有工具僅產出建議，無部署能力）

## Resolved Questions

- ~~[R1] 自訂域名 / 網站啟用狀態~~ — API 回報誤差，`site_url` 和 `home` 均為 `https://yololab.net`，域名綁定正常
- ~~[R6] 關鍵字研究工具可行性~~ — 可行：Google Suggest 爬蟲（免費發現）+ GSC 現有數據 + DataForSEO API（~$0.01/query 驗證搜尋量）
- ~~[R5] 301 重定向實作方式~~ — Redirection plugin 已安裝啟用，可直接使用
- ~~[R10] API rate limit~~ — 未被官方文件化，降級為 Planning 階段漸進式測試（10→20→30 篇/天）

## Outstanding Questions

### Deferred to Planning

- [Affects R7][Needs research] AI 生成內容的最佳 prompt 策略——如何從現有 2,728 篇文章萃取 YOLO LAB 寫作風格作為 few-shot examples
- [Affects R7][Technical] 模型選擇（Haiku vs Sonnet vs Opus）的品質/成本權衡——需用小批量 A/B 測試決定
- [Affects R8][Technical] 品質閘門四項指標的權重分配與門檻值，需從現有高表現文章的 GSC 數據反推
- [Affects R5][Technical] WordPress.com Atomic 上 301 重定向的實作方式——是否需要 plugin 或 server-level 配置
- [Affects R11][Needs research] X API、Threads API、LINE Messaging API 的免費層級額度（X 免費層 1,500 tweets/月可能不夠）
- [Affects R9][Technical] Topic Cluster 的最佳規模——每個 cluster 的 pillar/article 比例需要根據現有分類結構設計

## Next Steps

→ 所有 blocking questions 已解決，可進入 `/ce:plan` 進行結構化實施規劃
