---
title: "feat: YOLO LAB 10x 流量成長優化計畫 — Phase 1-3 全面實施"
type: feat
status: active
date: 2026-04-08
origin: docs/brainstorms/2026-04-08-10x-traffic-growth-requirements.md
deepened: 2026-04-08
---

# YOLO LAB 10x 流量成長優化計畫 — Phase 1-3 全面實施

## Overview

YOLO LAB (yololab.net) 目前月瀏覽量 34,270，目標 6-12 個月達到 342,700+（10x）。本計畫整合存量優化、程式化內容擴張、多渠道分發三大槓桿，突破單純 SEO 優化的 4x 天花板。

**分階段路線圖：**
- **Phase 1 (Month 1-2)：基底優化** — 完成 ~1,800 篇文章 SEO、首頁重構、內鏈網路 → 預期 3-4x（~100-130K）
- **Phase 2 (Month 3-6)：程式化內容擴張** — AI 生成 3,000-5,000 新文章、Topic Cluster 架構、自動品質閘門 → 預期 6-8x（~200-270K）
- **Phase 3 (Month 6-12)：多渠道分發放大** — X/Threads/LINE OA 自動化、RSS-to-Social、數據驅動迭代 → 預期 10x+（~340K+）

## Problem Frame

YOLO LAB 目前面臨**流量成長停滯**的三個根本原因：

| 問題 | 現狀 | 影響 |
|------|------|------|
| **內容體積瓶頸** | 2,728 篇文章存量，無新增 | 搜尋覆蓋有限，長尾關鍵字空白 |
| **存量 SEO 不完整** | 898 篇已優化，1,830 篇待處理 | 估計 50-80% 流量損失在未優化文章 |
| **站內結構缺陷** | 無首頁策略、無內鏈網路、無 Schema | 爬蟲預算浪費，Link equity 分散，E-E-A-T 信號缺失 |
| **內容發現性差** | 首頁 = blog roll，分類頁無描述 | 不利於用戶導航，Google 無法理解分類權重 |

**存量優化極限：** 完成 Phase 1 預期流量 3-4x（130K），達到現有內容結構下的最大值。進一步成長需 Phase 2-3 的新內容 + 多渠道策略。

## Requirements Trace

- **R1.** 完成剩餘 ~1,800 篇文章的 SEO 優化（Meta title/description、Schema markup、OG tags），使用既有 batch optimizer 工具鏈，目標 1 個月完成，成本 ≤ $30
- **R2.** 部署首頁重構：靜態首頁 + 5 個分類 Hub 區塊 + 完整首頁 Schema（WebSite + SearchAction + Organization），提升首頁 SEO score ≥ 90，啟用 Google Sitelinks Search Box
- **R3.** 部署內部連結網路：消除 1,695 篇孤兒文章，每篇至少 3 個內鏈（1 pillar + 2 cluster peers），提升 crawl budget 效率
- **R4.** 執行標籤架構整合：5,000+ 標籤 → 150 個 super-tags，對應 5 大分類 Hub，完善分類頁面
- **R5.** 建立程式化內容生成管線：識別 3,000-5,000 個未覆蓋的長尾關鍵字，自動生成符合 YOLO LAB 風格的文章，包含 Meta/Schema/內鏈，每日發布 5-8 篇（避免 Google 偵測內容暴增）
- **R6.** 建立自動化品質檢查閘門：可讀性評分、事實核查、SEO 評分、重複檢測，確保新文章品質 ≥ 70/100
- **R7.** 建立多渠道分發自動化：新文章自動發布至 X、Threads、LINE OA，RSS-to-Social 同步，實現零邊際成本的內容放大
- **R8.** 建立數據驅動迭代系統：監控 GSC + GA4，自動識別高潛力文章進行升級、低表現文章進行合併/刪除

## Scope Boundaries

**In Scope：**
- SEO 優化：Tier 1-4 全覆蓋（2,728 篇）
- 首頁 + 分類頁重構（FSE 模板設計）
- 內部連結批量腳本（semantic clustering）
- AI 驅動的內容生成（關鍵字 → 文章）
- 自動化品質檢查（非手動審稿）
- 多渠道分發自動化（API 整合）
- GSC/GA4 監控儀表板

**Out of Scope：**
- 付費廣告（Google Ads、社群廣告）
- 人工編輯審稿（全自動流程）
- 網站平台遷移（維持 WordPress.com Atomic）
- 非繁體中文內容
- 影片內容製作（僅文字 + 圖片）
- 高於 AI 生成的人工創意內容

## Context & Research

### Existing Code & Patterns

**SEO 優化工具：**
- `scripts/yolo-lab-seo-optimizer-v3.js` — 企業級 4 功能 SEO 優化器（Meta/Schema/OG/Links）
- 批量模式：10-50 篇/批，500-1000ms 延遲，state JSON 檢查點，100% 成功率（已驗證 2,800 篇）
- 成本：Claude Opus 每篇 $0.10，Sonnet 每篇 $0.003（Haiku tier）

**WordPress.com MCP 集成：**
- 狀態：`.mcp.json` 已配置，但無 JavaScript 客戶端代碼調用 `posts.update`
- 認證：JWT token 與 WordPress.com REST API OAuth2 不相容（已識別問題）
- 備選方案：直接 REST API（cookie-jar 認證）或 `gh api` proxy

**批量處理基礎設施：**
- State 管理：`state_phase{X}_tier{Y}.json` 檢查點，支援 `--resume {date}` 恢復失敗
- 重試邏輯：3 次重試 + 指數退避（2s, 4s, 8s）
- Rate limiting：500-1000ms 批次延遲，實測安全在 WordPress.com API

**現有 Phase 1 成果：**
- ✅ 2,800 篇文章已優化（成本 $280）
- ✅ 首頁架構計畫已完成（docs/plans/2026-04-08-002-feat-homepage-seo-architecture-plan.md）
- ✅ GSC 監控框架就位（14 天檢查點）
- ⚠️ 1,830 篇文章尚待優化
- ⚠️ 內部連結網路僅部分實施（100 篇試點）

### Institutional Learnings

**Tier 基優化框架（已驗證）：**
- Tier 1 (P0)：200 篇高流量文章 → 深度優化（6 維）→ ROI 5x
- Tier 2 (P1)：600 篇中流量文章 → 標準優化（4 維）
- Tier 3 (P2)：1,200 篇低流量文章 → 簡化優化（2 維）→ 成本 50% 降低
- Tier 4 (P3)：728 篇極低流量文章 → 範本優化（自動化）

**GSC 監控教訓：**
- ⚠️ 首 7 天內排名可能下降 3-5 位（re-evaluation 期間），不信第 7 天數據
- ✅ 14 天後穩定，CTR 改善 +8-15%（Phase 1 實測）
- ✅ 30 天月度流量改善 +20-30%（Phase 1 目標）

**API 整合陷阱：**
- ❌ JWT 認證無法用於 WordPress.com REST API（需 OAuth2）
- ✅ 直接 REST API + cookie-jar 認證有效但易碎
- ✅ WordPress.com MCP 是長期解決方案（認證封裝，已配置 Bearer token）

**AI 內容品質（29 個反模式）— `docs/batch1-2-humanization-report.md`：**
- 三大類需消除：(1) 意義膨脹（"深度分析"、"完整評測"）(2) 模糊歸因（"揭秘"、"達人分享"）(3) 推銷語言（"必看"、"首選"）
- YOLO LAB 風格：直接、台灣用語、疑問句標題（"誰贏？"、"真的假的？"）、對話式 meta
- **此清單必須嵌入 Phase 2 內容生成 prompt**

**成本模型（2026-04 更新）：**
- Claude Batch API：$0.003/call vs Real-time $0.05-0.10/call（33x 差距）
- 推薦：Sonnet 4.5 + Batch API + prompt caching → 5,000 篇文章生成 ≈ $60-200
- Phase 1 SEO 優化實際成本基準：898 篇 = $2.70

### External References

- Schema.org/WebSite, SearchAction, CollectionPage 規格
- Google E-E-A-T 信號與 rich results 優化
- Topic Cluster hub-and-spoke 模型（2026 SEO 最佳實踐）
- WordPress 全網搜尋引擎優化 (Yoast SEO plugin/Jetpack)

## Key Technical Decisions

- **階段化風險管理：** Phase 1 基底優化（低風險、快速反饋） → Phase 2 內容擴張（中風險、成本 $50-150） → Phase 3 多渠道（高風險、但邊際成本低）
- **Tier 優化優先順序：** Tier 1 → Tier 2 → Tier 3，並行 GSC 監控，允許基於 14 天檢查點的 Phase 2 決定
- **API 認證方案：** 使用 WordPress.com Application Passwords（WP 5.6+ 原生支援，不過期，適合長期無人值守發布）。cookie-jar 僅作為 fallback。MCP 已配置但 JWT 有過期限制，不適合長期自動化
- **內容生成品質閘門：** 自動評分 ≥ 70/100（可讀性 + SEO + 重複檢測），無手動審稿，通過即發布
- **多渠道分發優先級：** Threads API (免費) > X API ($0.01/tweet, pay-per-use since 2026/2) > LINE Messaging API (按量計費)。X 免費方案已停止對新開發者開放
- **內容生成成本策略：** Sonnet 4.5 + Batch API + prompt caching，預估 $60-200/5,000 篇（非原估 $630）
- **發布節奏：** 3-8 篇/天（非 30-50），避免 Google 偵測突然的內容暴增。先 draft 再排程 publish

## Open Questions

### Resolved During Planning

- **Q: WordPress.com 方案等級？** 假設 Atomic plan（已確認 blog_id: 133512998）
- **Q: GSC 資料可用性？** 已配置，有歷史數據，可獲取 CTR/impression/rank 數據
- **Q: Yoast SEO 插件是否可用？** Atomic plan 支援插件；確認後優先使用 Yoast API，否則用 custom meta
- **Q: 內容生成目標？** 3,000-5,000 新文章在 Phase 2 （6 個月內），即每月 500-833 篇

### Deferred to Implementation

- **關鍵字研究 API 方案選擇** — DataForSEO（$0.0006/SERP，$50 入金可用數月）+ Google Suggest 爬蟲（免費發現）+ GSC 既有數據（零成本）。已確認可行，執行時微調
- **AI 寫作風格提示詞設計** — 需從現有 2,728 篇文章萃取 few-shot examples（執行時調整）
- **品質閘門評分門檻細節** — 可讀性/SEO/重複的權重需基於 Phase 1 高表現文章反推（執行時調整）
- **Topic Cluster 最佳規模** — Pillar/article 比例需根據現有分類結構決定（執行時實驗）
- **社群 API 認證方案** — X/Threads/LINE 的免費層額度和認證流程（執行時研究）

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

### Phase 1-3 系統流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│ YOLO LAB 10x 流量增長系統架構                                    │
└─────────────────────────────────────────────────────────────────┘

Phase 1: 基底優化 (Month 1-2)
├─ [SEO Optimizer v3]
│  ├─ Input: 1,830 篇未優化文章 (Tier 1-4)
│  ├─ Process: Meta/Schema/OG 批量生成 (Claude API)
│  └─ Output: optimized posts → WordPress
├─ [Homepage Builder]
│  ├─ Input: 5 分類 + 品牌素材
│  ├─ Process: FSE block template 設計
│  └─ Output: static front page → WordPress
├─ [Internal Linker]
│  ├─ Input: 2,728 篇文章 (pillar map + semantic clustering)
│  ├─ Process: TF-IDF → Claude semantic ranking
│  └─ Output: 3+ links/article injected
└─ [Tag Aggregator]
   ├─ Input: 5,000+ 原始標籤
   ├─ Process: 聚合 → 150 super-tags
   └─ Output: category hub 對應

Phase 2: 程式化內容擴張 (Month 3-6)
├─ [Keyword Research Pipeline]
│  ├─ Input: GSC top queries + Google Suggest + People Also Ask
│  ├─ Process: 識別 3,000-5,000 未覆蓋關鍵字
│  └─ Output: keyword cluster database
├─ [Content Generator]
│  ├─ Input: keyword cluster + existing articles (few-shot)
│  ├─ Process: Multi-turn Claude API (title → body → meta → schema)
│  └─ Output: 100% AI-generated articles
├─ [Quality Gates]
│  ├─ Readability score (繁體中文支援)
│  ├─ Fact-checking (vs. source URLs)
│  ├─ SEO score (meta + schema validation)
│  └─ Duplicate detection
└─ [Auto Publisher]
   ├─ Process: 通過品質閘門 → 排程發布 (5-8 篇/日)
   ├─ Auto-tag + featured image + internal links
   └─ Output: WordPress posts

Phase 3: 多渠道分發放大 (Month 6-12)
├─ [Social Media Dispatcher]
│  ├─ Input: WordPress RSS feed (新發布文章)
│  ├─ Process: Platform-specific summarization (X/Threads/LINE)
│  └─ Output: automated posts to X/Threads/LINE OA
├─ [Analytics Monitor]
│  ├─ Input: GSC + GA4 data (daily)
│  ├─ Process: Identify high/low performers
│  └─ Output: content upgrade recommendations
└─ [Content Iteration Loop]
   └─ High-potential articles → Link upgrade → Reindex
       Low-performance articles → Merge or delete

GSC/GA4 Feedback Loop (Throughout)
└─ 14-day checkpoints → Decision gates (GO/NO-GO per phase)
```

### API Integration Stack

```
JavaScript Runtime (Node v24)
│
├─ [Claude API Client] (Anthropic SDK)
│  ├─ Content generation (multi-turn)
│  ├─ Semantic analysis (internal links)
│  └─ Quality scoring (readable.js compatible)
│
├─ [WordPress.com REST API] (direct or via MCP)
│  ├─ posts.list/update/create
│  ├─ categories.list
│  ├─ tags.list/update
│  └─ Custom meta field writes
│
├─ [Social Media APIs]
│  ├─ X API v2 (tweets, rate limits)
│  ├─ Threads API (thread posts)
│  └─ LINE Messaging API (OA broadcasts)
│
└─ [Analytics APIs]
   ├─ Google Search Console API (query/page/device data)
   └─ Google Analytics 4 API (events, traffic source)
```

## Implementation Units

### Phase 1: 基底優化 (Month 1-2)

---

- [ ] **Unit 1.1: 完成 Tier 1 文章 SEO 優化**

**Goal:** 優化 Tier 1 (P0) 200 篇高流量文章，應用 6 維優化（Meta/Schema/OG/Links/Alt/FAQ），作為 Phase 1 基準，獲得 14 天反饋。

**Requirements:** R1

**Dependencies:** None (parallel with other Phase 1 units)

**Files:**
- Modify: `scripts/yolo-lab-seo-optimizer-v3.js` — 確認 `--phase 1 --tier 1` 模式可用
- Modify: `seo-optimization-output/state_phase1_tier1.json` — Tier 1 檢查點
- Create: `seo-optimization-output/report_phase1_tier1.json` — Tier 1 報告

**Approach:**
- 運行 `node scripts/yolo-lab-seo-optimizer-v3.js --phase 1 --tier 1 --dry-run --sample 5` 驗證 5 篇試點
- 修正提示詞或 API 問題後，執行完整 Tier 1 批次（200 篇，10 篇/批，延遲 1000ms）
- 每 50 篇保存 state JSON，支援 `--resume {date}` 復原
- 輸出包含：成功數/失敗數/跳過數、每篇成本、cumulative token 計數
- **Timeline:** 1-2 天（預期 200 篇 ≈ $20-30 成本）

**Patterns to follow:**
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 state 管理、retry 邏輯、batch 模式
- `seo-optimization-output/report_phase*.json` 的報告格式

**Test scenarios:**
- Happy path: Tier 1 全部 200 篇成功優化，無 API 錯誤
- Edge case: 少數文章缺 excerpt/metadata 時，使用 fallback template（不 skip）
- Error path: 429 rate limit → exponential backoff，最多 3 次重試
- Integration: 優化後 WordPress 更新，`posts.update` 成功寫入 meta 欄位

**Verification:**
- `curl https://yololab.net/posts/{TIER1_ID} | grep '<meta name="description"'` 返回新 description
- Google Rich Results Test 對 Tier 1 樣本文章通過（無 schema error）
- Cost tracking 輸出顯示 token/cost per post

---

- [ ] **Unit 1.2: 部署首頁靜態頁面 + FSE 區塊結構**

**Goal:** 建立靜態首頁 Page，設計 FSE block 結構（Cover hero + Columns category hubs + Query loops），並設定為 Front Page。

**Requirements:** R2

**Dependencies:** None

**Files:**
- Create: `scripts/homepage-builder.js` — 使用 wpcom-mcp-content-authoring 或直接 REST API 建立首頁
- Modify: WordPress Settings → Reading → static front page （via admin UI 或 API）
- Reference: `docs/plans/2026-04-08-002-feat-homepage-seo-architecture-plan.md` (already completed — use Unit 1-3 design)

**Approach:**
- 使用 `wpcom-mcp-content-authoring pages.create` 建立 title="首頁" 的 Page
- Page content 為完整 FSE block markup（Cover + Columns + Query blocks），見 High-Level Design 或参考 2026-04-08-002 plan
- 5 個分類 hub 的 Query Loop 用 `{"categoryIds": [FILM_ID, ...]}` 篩選
- Hero section H1 = "YOLO LAB｜解構科技邊際與媒體娛樂的數據實驗室"
- 執行後設定為 Front Page，設定 `/blog/` 為 posts page
- 透過 wpcom-mcp 取得 edit link + preview link

**Patterns to follow:**
- `docs/plans/2026-04-08-002-feat-homepage-seo-architecture-plan.md` Unit 1 的設計決策和 FSE block 模板
- `scripts/batch-publisher.py` 的 page creation REST API pattern

**Test scenarios:**
- Happy path: Page 建立成功，設為 Front Page，預覽顯示完整 hero + 5 個分類 hub
- Edge case: 已存在同名 page 時，返回既有頁面 ID（不重複建立）
- Integration: 首頁 → 任意分類頁 → 文章 ≤ 3 clicks
- Verification: `curl https://yololab.net/ | grep '<h1'` 只有 1 個 H1；5 個 H2 (Film/Music/Tech/Sports/Entertainment) 可見

**Verification:**
- 首頁 Lighthouse SEO score ≥ 85（內部測試）
- 無 broken images/links（WebFetch 檢驗）
- 分類 hub query loops 顯示正確篇數（3-4 篇/hub）

---

- [ ] **Unit 1.3: 部署首頁 Schema (WebSite + SearchAction + Organization)**

**Goal:** 為首頁注入完整 JSON-LD @graph，包含 WebSite + SearchAction（啟用 Sitelinks Search Box）+ Organization + WebPage。

**Requirements:** R2

**Dependencies:** Unit 1.2（首頁靜態頁面需先存在）

**Files:**
- Create: `scripts/schema-homepage-injector.js` — 生成並注入首頁 schema
- Create: `data/homepage-schema.json` — schema 模板
- Modify: 首頁 Page content（via Custom HTML block）

**Approach:**
- 優先嘗試 Yoast SEO API 設定首頁 schema（若 Business plan 支援）
- 次選：透過 `wpcom-mcp-content-authoring posts.update` 於首頁 content 頂部注入 `<script type="application/ld+json">` block
- Schema @graph 含 4 個物件：WebSite、Organization、WebPage、SearchAction (potentialAction)
- SearchAction target: `https://yololab.net/?s={search_term_string}`
- 驗證：Google Rich Results Test `https://yololab.net` 通過

**Patterns to follow:**
- `docs/plans/2026-04-08-002-feat-homepage-seo-architecture-plan.md` Unit 3 的 schema @graph 設計
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 schema generation 模式

**Test scenarios:**
- Happy path: 首頁 `<head>` 含 `@type: WebSite` + SearchAction，Google Rich Results Test 通過
- Edge case: Yoast 已自動生成 WebSite schema → 僅補充 SearchAction（避免重複）
- Integration: Google 搜尋 "yololab" 顯示 Sitelinks Search Box（可能需 2 週）
- Verification: Rich Results Test 無錯誤（warning 可接受）

**Verification:**
- `curl https://yololab.net | grep -A 20 '"@type": "SearchAction"'` 有結果
- Schema Markup Validator 檢驗通過
- Google Search Console > Experience > Enhancements > Sitelinks Search Box 顯示可用

---

- [ ] **Unit 1.4: 部署全站麵包屑 BreadcrumbList Schema**

**Goal:** 為 single post 和 category archive 模板添加 BreadcrumbList JSON-LD，改善 SERP 顯示。路徑：Home > [Category] > [Article]。

**Requirements:** R2, R3

**Dependencies:** Unit 1.2（首頁 URL 確認後）

**Files:**
- Modify: WordPress Site Editor `single.html` template (add breadcrumb block)
- Modify: WordPress Site Editor `category.html` template (add breadcrumb block)
- Create: `scripts/breadcrumb-schema-validator.js` — 批量驗證代表性頁面

**Approach:**
- 在 FSE Site Editor 的 single post template 添加 `wp:yoast-seo/breadcrumbs` block（Yoast available）
- 若 Yoast 不可用，使用 `wp:rank-math/breadcrumb` 或 custom JSON-LD 注入
- 麵包屑路徑規則：
  - Single posts: `Home > [Category] > [Article Title]`
  - Category archives: `Home > [Category]`
- 透過 `wpcom-mcp-site-editor-context` 確認 theme 支援的 blocks
- 驗證：批量檢驗 10 篇隨機文章的 BreadcrumbList schema

**Patterns to follow:**
- 現有 site 已有 Article schema → breadcrumb 補充，不替換
- `docs/plans/2026-04-04-unit1-2-schema-deployment-plan.md` 的 Yoast 設定 pattern

**Test scenarios:**
- Happy path: 5 篇隨機文章的 BreadcrumbList 路徑正確
- Edge case: 文章屬多分類時，breadcrumb 使用 primary category
- Integration: Google SERP 14 天後顯示麵包屑（需時間索引）
- Verification: Google Rich Results Test 對 10 篇文章 + 5 個分類全部通過

**Verification:**
- `scripts/breadcrumb-schema-validator.js --sample 10` 通過率 ≥ 90%
- Single post template 在 Site Editor 可見 breadcrumb block
- 14 天後在 Google SERP 確認麵包屑顯示

---

- [ ] **Unit 1.5: 執行內部連結批量腳本 (Tier 1 優先)**

**Goal:** 為 Tier 1 200 篇高流量文章注入 ≥3 個內部連結（1 pillar + 2 cluster peers），建立站內連結網路。

**Requirements:** R3

**Dependencies:** Unit 1.2（分類結構確認）+ Unit 1.1（SEO 優化完成）

**Files:**
- Create: `data/pillar-map.json` — {category_slug: pillar_post_id} 映射
- Create/Modify: `scripts/internal-linker.js` — 批量內部連結注入腳本（若不存在）
- Create: `data/link-audit-results.json` — 執行後輸出

**Approach:**

**Pillar Page 選定：**
- 從 Tier 1 清單中每個分類選最高 view count 的 1 篇
- Pillar 理想特徵：字數 ≥ 1,500，覆蓋分類核心主題，非時效性
- 初始候選（待確認）：Film/Music/Tech/Sports/Entertainment 各 1 篇

**internal-linker.js 架構（擴展自 v3 optimizer）：**
- `--phase audit` — 統計 Tier 1 文章的 outgoing internal links，輸出 link-audit-results.json
- `--phase add --tier 1` — 讀 pillar-map.json，為每篇文章插入 3 條內部連結：
  1. 1 條 → pillar page（位於文章前 1/3）
  2. 2 條 → 同分類 cluster peers（語義相似）
- `--dry-run` — 輸出 proposed-links.json，供人工確認
- State 管理：state JSON 支援 `--resume {date}` 復原
- Rate limiting：10 篇/批，延遲 1000ms

**連結規則（硬性限制）：**
- Anchor text：描述性 partial-match（無「點這裡」「閱讀更多」）
- Outgoing internal links ≤ 8/article
- Pillar-pointing link 置於文章前 1/3
- Cross-category links ≤ 30%（保持主題聚焦）

**Patterns to follow:**
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 state JSON、retry、--dry-run、--resume
- Semantic similarity：TF-IDF keyword filter → Claude ranking top 5

**Test scenarios:**
- Happy path (audit): 200 篇 Tier 1 全部統計完，link-audit-results.json 含 outgoing/incoming 計數
- Happy path (dry-run): proposed-links.json 每篇 ≥ 3 新連結，anchor text 有效
- Edge case: 文章已有 ≥8 links → skip，記錄至 skipped.json
- Edge case: Pillar page 本身不自指
- Error path: 429 rate limit → exponential backoff，最多 3 retry
- Integration: add phase 完成後，抽驗 5 篇，posts.update 返回 200，content 含新 `<a>` 標籤

**Verification:**
- audit 完成後 link-audit-results.json 可讀
- dry-run 完成後 proposed-links.json 每筆含 {postId, anchorText, targetUrl, insertionContext}
- 人工確認後執行 add phase，更新率 ≥ 95%

---

- [ ] **Unit 1.6: 執行標籤架構整合與優化**

**Goal:** 聚合 5,000+ 原始標籤 → 150 個 super-tags，對應 5 大分類 Hub，完善分類頁面的標籤導航。

**Requirements:** R4

**Dependencies:** Unit 1.2（分類結構確認）

**Files:**
- Create: `scripts/tag-aggregator.js` — 聚合標籤，建立 tag → category 映射
- Create: `data/tag-mapping.json` — {original_tags: [...], super_tag: "...", category: "..."}
- Modify: WordPress category pages — 添加 related tags widget

**Approach:**
- **Pre-operation backup**：備份所有 2,728 篇文章的 `{post_id: [original_tag_ids]}` 至 `backups/pre_tag_consolidation_backup.json`，支援完整回滾
- 運行 `wpcom-mcp-content-authoring tags.list` 取得全部 5,000+ 標籤及使用頻率
- 按分類聚合：
  - Film 類：300-400 原始標籤 → 30 super-tags
  - Music 類：300-400 → 30 super-tags
  - Tech 類：400-500 → 35 super-tags
  - Sports 類：300-400 → 30 super-tags
  - Entertainment 類：400-500 → 35 super-tags
- Super-tag 命名規則：`[category]:[subtopic]`（e.g., `film:hollywood`, `music:k-pop`）
- 建立 original_tag → super_tag 映射，批量更新文章標籤（via posts.update）
- 在各分類頁添加「相關標籤」區塊，顯示 top 10 super-tags

**Patterns to follow:**
- `scripts/bulk_tags_final.py` 的 tag API 批量操作 pattern
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 batch 和 state 管理

**Test scenarios:**
- Happy path: 5,000+ 標籤成功聚合為 150 super-tags，tag-mapping.json 無重複
- Edge case: 孤兒標籤（0 篇文章使用）→ 不聚合，保留為低頻標籤
- Integration: 聚合後分類頁的 related tags widget 顯示正確 super-tags
- Verification: 隨機抽驗 100 篇文章，新標籤分配正確

**Verification:**
- `wpcom-mcp-content-authoring tags.list | jq '.tags | length'` ≈ 150 super-tags（非原始 5,000+）
- 分類頁的 related tags widget 可見且 clickable
- Tag 雲圖視覺化顯示分布（可選）

---

### Phase 2: 程式化內容擴張 (Month 3-6)

*Note: Phase 2 execution 基於 Phase 1 的 14-day GO/NO-GO checkpoint 結果。若 Phase 1 達成 CTR +15% 且無排名降權，則進行 Phase 2。*

---

- [ ] **Unit 2.1: 建立關鍵字研究自動化管線**

**Goal:** 識別 3,000-5,000 個 YOLO LAB 尚未覆蓋的長尾關鍵字（月搜量 30-500），構建關鍵字群集資料庫。

**Requirements:** R5

**Dependencies:** Unit 1.1-1.6 完成 + Phase 1 GO decision

**Files:**
- Create: `scripts/keyword-research-pipeline.js` — 多源關鍵字蒐集（Google Suggest + People Also Ask + GSC existing queries）
- Create: `data/keyword-clusters.json` — {keyword, search_volume, cpc, competition, topic_cluster}
- Create: `scripts/keyword-clustering.js` — 語義聚類（TF-IDF + Claude semantic grouping）

**Approach:**
- **Source 1: DataForSEO API** — Keywords For Site + Related Keywords endpoint（每查詢最多 4,680 建議），$0.0006/SERP request，含搜尋量/CPC/競爭度。$50 入金可查 ~80,000 個關鍵字
- **Source 2: Google Suggest** — 輸入 Tier 1 文章的主要關鍵字 + a-z 字母展開，爬取自動完成建議。需 proxy rotation + 1-3s 間隔避免封鎖
- **Source 3: GSC existing queries** — 已有排名但未點擊的查詢（GSC API），零成本高機會
- **Source 4: People Also Ask** — 爬取 SERP 中的「其他人也在問」區塊（可用 Serper.dev 免費方案 2,500 次/月）

**關鍵字聚類：**
- TF-IDF filter → 同義詞聚合
- Claude API semantic grouping → top 10 clusters per category
- 為每個 cluster 選擇 pillar keyword（搜量最高）

**輸出：**
- keyword-clusters.json：{keyword, search_volume: est., cpc: $, competition: low/med/high, pillar_keyword: bool, topic_cluster: "...", content_angle: "..."}
- **預計成果：** 3,000-5,000 個可攻略的長尾關鍵字，聚為 300-500 個內容 cluster

**Patterns to follow:**
- Google Suggest/People Also Ask 爬蟲（rate limit friendly，5-10 req/min）
- GSC API 整合（OAuth2 setup）

**Test scenarios:**
- Happy path: 從 5 個分類各挑 1 個 seed keyword，生成 200+ 子關鍵字，無重複
- Edge case: 某 cluster 關鍵字都已被現有文章覆蓋 → 標記 skip，不重複生成
- Verification: keyword-clusters.json 可讀，每個 cluster 含 pillar_keyword 和 top 10 variations

**Verification:**
- keyword-clusters.json 包含 3,000+ 項，競爭等級分布合理
- GSC gap analysis：抽驗 50 個 existing queries（低點擊），確認可作為新內容的 target

---

- [ ] **Unit 2.2: 建立 AI 內容生成管線**

**Goal:** 根據 keyword-clusters.json，自動生成符合 YOLO LAB 風格的 3,000-5,000 新文章，包含 title、body、meta、schema、internal links。

**Requirements:** R5

**Dependencies:** Unit 2.1（keyword clusters 就位）+ Unit 1.1-1.6（style examples + linking targets）

**Files:**
- Create: `scripts/content-generator.js` — Multi-turn Claude API，基於 keyword cluster 生成文章
- Create: `data/style-examples.json` — Few-shot examples（從現有 Tier 1 文章萃取）
- Modify: `scripts/yolo-lab-seo-optimizer-v3.js` — 新增 `--gen` phase 用於新文章 meta/schema
- Create: `data/generated-articles/` — 存放中間產出和最終文章

**Approach：**

**風格提示詞設計：**
- 從現有 200-400 篇高表現文章中萃取 few-shot examples（title/excerpt/writing tone）
- **嵌入 29 個 AI 反模式清單**（見 `docs/batch1-2-humanization-report.md`）作為 negative examples
- YOLO LAB 風格指引：直接/不廢話、台灣在地用語、疑問句標題、對話式 meta description
- 每篇需有至少 1 個**獨特資料維度**（數據比較、時間線、排名等），避免被判為樣板內容
- Prompting 策略：
  1. Turn 1：生成 3 個 title 候選（55-60 chars，含主關鍵字）
  2. Turn 2：根據選中 title 生成文章正文（1,500-2,500 words，分段含 subheadings）
  3. Turn 3：生成 meta description（120-160 chars，含 CTA）
  4. Turn 4：生成 schema markup（Article + Author + datePublished）
  5. Turn 5：推薦 internal links（3-5 條，含 pillar 和 cluster peers）

**Batch 處理：**
- 批量大小：50 篇/批（比 Tier 1 優化大，因為新文章無既有 API 延遲）
- 並發：1-2 concurrent turns（避免超過 Claude API rate limit）
- 成本追蹤（Batch API + Sonnet 4.5 + prompt caching）：每篇 ≈ $0.01-0.04
- 全批預估成本：3,500 篇 × $0.03 = **$105**（Batch API），Real-time fallback ≈ $350-630
- **使用 prompt caching**：style guide + anti-patterns 作為 system prompt 快取，節省 90% 重複 context 成本
- **注意**：現有程式碼僅使用同步 `messages.create`，Batch API (`messages.batches.create`) 需從頭開發——含 JSONL 請求生成、輪詢完成、結果解析、部分失敗處理。這是一個獨立子系統，非配置變更

**輸出格式：**
```json
{
  "keyword_cluster": "film:hollywood-2026",
  "pillar_keyword": "好萊塢電影 2026",
  "title": "2026 好萊塢大製作電影推薦｜10 部年度必看 A 級巨星新作",
  "body": "...(1,500+ words)...",
  "meta_description": "...",
  "schema": {...},
  "internal_links": [...]
}
```

**Patterns to follow:**
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 multi-turn 設計
- Few-shot prompting 的風格提示詞設計（從現有文章反推）

**Test scenarios:**
- Happy path: 50 篇試點生成，title/body/meta/schema 皆有效，readability score ≥ 70
- Edge case: 某關鍵字群集語境不清 → Claude 生成通用內容（通過品質閘門即可發布）
- Error path: 429 rate limit → 自動降速至 1 turn/2s，exponential backoff
- Integration: 生成文章通過品質閘門後，準備發布

**Verification:**
- 50 篇試點通過品質閘門（Unit 2.3）
- 人工抽查 5 篇，內容品質 ≥ 70/100
- Meta + schema 驗證無誤，可直接導入 WordPress

---

- [ ] **Unit 2.3: 建立自動化品質檢查閘門**

**Goal:** 為 Unit 2.2 生成的文章實施多維品質檢查（可讀性、事實核查、SEO 分數、重複檢測），確保發布品質 ≥ 70/100。

**Requirements:** R6

**Dependencies:** Unit 2.2（生成文章就位）

**Files:**
- Create: `scripts/quality-gate.js` — 品質評分引擎
- Create: `data/quality-scores.json` — 每篇文章的評分細項
- Create: `scripts/fact-checker.js` — 事實核查模組（vs. source URLs）
- Create: `scripts/duplicate-detector.js` — 重複檢測模組

**Approach：**

**品質評分維度（0-100 scale）：**

1. **可讀性評分 (Readability, 25 pts)**
   - 工具：readable.js (繁體中文支援) 或 Claude API 評估
   - 指標：段落長度、句子複雜度、常用詞彙比例
   - 門檻：≥ 18 pts (72/100)

2. **SEO 評分 (SEO, 25 pts)**
   - Title 包含主關鍵字：5 pts
   - Meta description 120-160 chars：5 pts
   - Subheading H2/H3 結構完整：5 pts
   - Internal links ≥ 3 條：5 pts
   - Schema markup 有效：5 pts
   - 門檻：≥ 18 pts (72/100)

3. **來源引用完整性 (Source Citation, 25 pts)**
   - 自動檢測：文中是否包含可連結的外部來源（URL 或具名引用）
   - 評分：≥3 個有效來源引用 25 pts，1-2 個 15 pts，無引用 5 pts
   - AI 反模式檢測：掃描 29 個已知反模式（`docs/batch1-2-humanization-report.md`），超過 3 個扣 10 pts
   - 門檻：≥ 18 pts (72/100)

4. **重複檢測 (Duplicate, 25 pts)**
   - vs. 現有 2,728 篇文章：相似度 < 20%（TF-IDF cosine similarity）
   - vs. 本批生成文章：無完全重複（hash-based）
   - 評分：無重複 25 pts，輕度重複 (<20%) 10 pts，高度重複 (>20%) 0 pts
   - 門檻：≥ 18 pts (72/100)

**品質閘門規則：**
- **綠色 (Pass)：** 總分 ≥ 70，進入自動發布佇列
- **黃色 (Review)：** 總分 60-69，送入人工審稿佇列（非自動，需手動確認）
- **紅色 (Reject)：** 總分 < 60，不予發布，標記為 rejected

**預期通過率：** 85-90%（基於 Phase 1 高表現文章的標準）

**Patterns to follow:**
- readable.js 用於繁體中文可讀性評估
- 向量相似度計算用於重複檢測（TF-IDF cosine similarity）

**Test scenarios:**
- Happy path: 50 篇試點中 42-45 篇通過品質閘門 (84-90% pass rate)
- Edge case: 某篇事實核查失敗 (day/date 錯誤) → 降級至黃色，等待人工確認
- Edge case: 與現有文章重複度 > 20% → 紅色拒絕
- Error path: readable.js 繁體支援不足 → fallback 至 Claude API 評估 (成本增加 $0.001/篇)
- Integration: 通過品質閘門的文章進入 Unit 2.4 自動發布佇列

**Verification:**
- quality-scores.json 包含每篇的 4 維評分細項
- 人工抽查 20 篇黃色文章，確認事實正確率 ≥ 80%
- 通過率達到 80%+ 作為 Phase 2 GO signal

---

- [ ] **Unit 2.4: 建立 Topic Cluster 架構與內部連結系統**

**Goal:** 為生成的文章建立 hub-and-spoke Topic Cluster，每個 pillar page 對應 5-15 篇 cluster articles，自動建立雙向內鏈。

**Requirements:** R5, R6

**Dependencies:** Unit 2.1-2.3（keyword clusters + 生成文章通過品質）

**Files:**
- Create: `data/topic-clusters.json` — {pillar_keyword, pillar_post_id, cluster_articles: [{id, title, relationship}], internal_links: [...]}
- Modify: `scripts/internal-linker.js` — 新增 `--phase cluster` 模式用於 cluster 內部連結

**Approach：**

**Cluster 設計：**
- 每個 cluster 1 pillar page + 5-15 cluster articles
- Pillar page = keyword-clusters.json 中的 pillar_keyword 對應的文章（新生成或 Tier 1 既有）
- Cluster articles = 同一 cluster 下的其他關鍵字對應的文章（新生成）

**內部連結策略（Hub-and-Spoke）：**
- Pillar → Cluster：每個 cluster article 的第 1 段落內包含指向 pillar 的連結
- Cluster → Pillar：pillar page 正文中包含指向 5-15 個 cluster articles 的連結（分散於各段落）
- Cluster ↔ Cluster：同 cluster 內的 articles 互相連結（2-3 條/篇，語義相關）

**自動化流程：**
- 讀取 keyword-clusters.json，為每個 cluster 指定 pillar page
- 對新生成的文章，自動注入 pillar 連結（位置固定：第 1-2 段落）
- 對 pillar page，自動注入 cluster 連結（分散於正文，每 300 字 1 條）
- 驗證：outgoing links 不超 8/篇，cross-cluster links ≤ 30%

**輸出：**
- topic-clusters.json：300-500 個 cluster 的完整定義
- 內部連結注入至生成文章（via posts.update），pillar page 更新完成

**Patterns to follow:**
- Unit 1.5 (internal-linker.js) 的連結注入 pattern
- TF-IDF + Claude ranking for 語義相關性

**Test scenarios:**
- Happy path: 選中 1 個 cluster（e.g., "film:hollywood"），pillar + 10 cluster articles 完整生成，雙向連結注入成功
- Edge case: 某 cluster 只有 pillar + 2 articles（<5）→ 不強制補充，按現況生成 cluster
- Integration: Pillar page 在 Category hub 和首頁特色區域顯示
- Verification: 隨機抽查 5 個 cluster，驗證連結完整性

**Verification：**
- topic-clusters.json 包含 300+ clusters，每個 cluster 平均 8-10 articles
- Pillar pages 在分類頁和首頁優先顯示
- 抽驗 10 篇 cluster articles，內鏈完整且有效

---

- [ ] **Unit 2.5: 自動化發布管線與排程系統**

**Goal:** 將通過品質閘門的文章自動排程發布至 WordPress，達到 5-8 篇/天的穩定產出，包括自動分類、標籤、特色圖片、內鏈。

**Requirements:** R5, R6

**Dependencies:** Unit 2.3（文章通過品質）+ Unit 2.4（topic cluster + internal links）

**Files:**
- Create: `scripts/auto-publisher.js` — 自動發布引擎
- Create: `data/publish-queue.json` — 發布排隊清單
- Create: `data/publish-schedule.json` — 發布時間表（5-8 篇/日）

**Approach：**

**發布前準備：**
1. 為新文章分配 category（基於 keyword cluster）
2. 為新文章分配 super-tags（基於 Unit 1.6 tag mapping）
3. 為新文章分配特色圖片：
   - 優先使用 Unsplash/Pixabay API 爬取相關圖片（free tier）
   - Fallback：使用 YOLO LAB 品牌色彩的佔位圖片
4. 注入 internal links（pillar + cluster peers）

**發布排程（2026 Google 最佳實踐 — 避免內容暴增偵測）：**
- 穩定節奏：**5-8 篇/天**（時間分散，每 2-3 小時 1 篇）
- 先以 `status: "draft"` 批量建立，再透過排程逐步改為 `publish`
- WordPress Batch endpoint：每批次 25 篇 draft 建立，間隔 2-5 秒
- 總計 3,500 篇 ÷ 7 篇/天 ≈ 500 天 → **需 Phase 2 延長至 Month 3-12，或接受較少篇數**
- 替代方案：Phase 2 先生成 1,500 篇高品質文章（5 篇/天 × 10 個月），Phase 3 持續擴張

**API 操作：**
- 使用 `wpcom-mcp-content-authoring posts.create` 或直接 WordPress REST API
- Batch 大小：10 篇/batch（發布不同於優化，無 rate limit 壓力）
- 狀態追蹤：publish-queue.json 記錄已發布的 post IDs，支援斷點復原

**驗證：**
- 每日監控 WordPress 後台 Posts list，確認新發布文章出現
- 每週抽查 5 篇，驗證分類/標籤/內鏈正確

**Patterns to follow：**
- `scripts/batch-publisher.py` 的 POST 發布 pattern
- State JSON 檢查點支援 `--resume`

**Test scenarios：**
- Happy path：10 篇試點發布，全部返回 201，post IDs 記錄在 publish-queue.json
- Edge case：某篇發布失敗（500 error）→ 記錄至 failed.json，支援人工重試
- Error path：429 rate limit → 自動延遲至 2s interval，降低發布速度
- Integration：發布後 WordPress RSS feed 包含新文章，Jetpack 發送通知

**Verification：**
- WordPress 後台 Posts 數量每日增加 5-8
- RSS feed 實時更新（https://yololab.net/feed/）
- 無 publish 錯誤日誌

---

### Phase 3: 多渠道分發放大 (Month 6-12)

*Note: Phase 3 execution 基於 Phase 2 的內容產出穩定性 (5+ 篇/日持續 2 週) 和品質指標 (≥70 score) 驗證。*

---

- [ ] **Unit 3.1: 自動化社群分發 (X/Threads/LINE)**

**Goal:** 每篇新發布文章自動生成平台適配的摘要文案，發布至 X、Threads、LINE Official Account，實現零邊際成本的內容放大。

**Requirements:** R7

**Dependencies:** Unit 2.5（新文章自動發布）

**Files：**
- Create：`scripts/social-dispatcher.js` — 多平台分發引擎（含 RSS 監控觸發）
- Create：`data/platform-templates.json` — X/Threads/LINE 的文案模板
- Create：`data/social-posts.json` — 發布記錄
- Create：`data/rss-seen.json` — 已處理的 RSS items（避免重複推送）

**Approach：**

**平台文案生成：**
1. **Threads（優先 — 免費）**
   - 格式：`{headline} {excerpt_100words} \n\n讀全文 → {link}`
   - 完全免費，2024/6 首次開放，2025/7 大幅擴充功能
   - 支援程式化發文、排程發布、分析數據 API
   - 認證：Meta Developer OAuth 2.0 + App Review

2. **X (Twitter) - $0.01/tweet（pay-per-use）**
   - 格式：`{Emoji} {hook} {key_point} 👉 [link] #tag`
   - **2026/2 起免費方案已停止對新開發者開放**，改為 pay-per-use
   - 成本：5-8 篇/天 × $0.01 = **$1.50-2.40/月**
   - Rate limit：24 小時視窗（非 15 分鐘），較嚴格

3. **LINE OA - 按量計費（Push API）**
   - 使用 Flex Message (carousel layout)
   - LINE Notify 已於 2025 終止，需用 Messaging API
   - 台灣市場特別有價值（LINE 為主流通訊 app）
   - Reply API 免費，Push API 按量計費

**發布邏輯：**
- WordPress `post_published` hook 觸發 → 從 post excerpt + meta 提取內容 → 生成平台文案 → 排隊發布
- 發布時機：文章發布後 30 分鐘（延遲以分散流量）
- 優先級：Threads（免費）> X（低成本）> LINE（針對台灣訂閱者）

**驗證：**
- 每日監控 X/Threads/LINE OA，確認新文章推文出現
- 追蹤點擊率 (CTR)，與 WordPress organic traffic 關聯

**Patterns to follow：**
- X API v2 authentication (Bearer token)
- Threads 非官方 API（推薦使用官方 Graph API）
- LINE Messaging API OAuth2

**Test scenarios：**
- Happy path：發布 1 篇文章，自動生成 3 份平台文案，成功發布至 X/Threads/LINE
- Edge case：文章無 excerpt → fallback 至前 200 字或標題
- Error path：X API 認證失敗 → 記錄至失敗隊列，人工重試
- Integration：社群分享點擊返回 WordPress（via UTM 追蹤）

**Verification：**
- Threads 帳號每日新發文 ≥ 1（免費）
- X 帳號每日新推文 ≥ 1（~$0.01/post）
- LINE OA 訊息推送每週 ≥ 3 次
- UTM 流量追蹤（campaign=yololab_social）
- RSS 監控延遲 < 20 分鐘（觸發機制內建於 social-dispatcher）

---

- [ ] **Unit 3.2: 數據驅動迭代系統**

**Goal：** 自動收集 GSC + GA4 數據，識別高潛力文章進行升級、低表現文章進行合併/刪除，形成持續優化的反饋迴路。

**Requirements：R8

**Dependencies：Unit 1-2 全部完成（基準線已建立）

**Files：**
- Create：`scripts/analytics-collector.js` — GSC + GA4 API 數據收集
- Create：`scripts/content-optimizer-v2.js` — 基於分析的文章升級引擎
- Create：`data/performance-report.json` — 每週/每月的績效報告

**Approach：**

**數據收集（週期：每週一次）：**
1. **Google Search Console API：**
   - Query：impressions、clicks、CTR、avg position（過去 28 天）
   - Filtered by: 頁面、設備類型、國家
   - 輸出：{page_url, impressions, clicks, ctr, avg_position}

2. **Google Analytics 4 API：**
   - Metrics：sessions、users、bounce_rate、avg_engagement_time、conversions
   - Dimensions：page_path、device_category、source
   - 輸出：{page_path, sessions, bounce_rate, engagement_time}

**績效分類：**
- **高潛力（High Potential）：** impressions 高 (>100/week) 但 CTR 低 (<3%)
  - 行動：升級 meta description 或添加 FAQ block，爭取 CTR +5-10%
  - 預期效果：clicks +30%

- **正常表現（Normal）：** impressions 適中，CTR 正常 (>5%)
  - 行動：內鏈升級（增加相關文章連結），提升 crawl 效率
  - 預期效果：indirect traffic +10-15%

- **低表現（Low Performer）：** impressions < 20/week，CTR < 2%，已 ≥ 6 個月
  - 行動：與類似文章合併、更新內容、或刪除（優化爬蟲預算）
  - 預期效果：crawl budget 集中，總體 visibility +5-10%

**自動化流程：**
1. 週一清晨執行 analytics-collector，抓取過去 28 天數據
2. 按高潛力/正常/低表現分類
3. 高潛力文章 → 自動生成升級提案（meta 改寫 + FAQ 添加），存至 upgrade-queue.json
4. 低表現文章 → 提交人工決策（不自動刪除）
5. 生成週報，發送至 Slack/email

**成本追蹤：**
- GSC API：free
- GA4 API：free
- Claude API 升級提案：$0.002/篇（估計每週 10-20 篇升級）

**Patterns to follow：**
- Google API client library (google-auth-library-nodejs)
- 時間戳管理避免重複

**Test scenarios：**
- Happy path：收集 100 篇文章的 GSC + GA4 數據，成功分類為高/正常/低
- Edge case：某篇文章無 GA4 數據（新發布）→ 跳過分類，3 週後重新評估
- Error path：GSC API 認證失敗 → 記錄為 pending，下週重試
- Integration：upgrade-queue.json 的文章自動進入人工審稿隊列（非自動執行）

**Verification：**
- 每週生成 performance-report.json，包含 3 個分類的文章清單
- 人工確認 5 篇高潛力文章的升級提案品質 ≥ 70/100
- 月報：低表現文章清單供決策

---

## System-Wide Impact

- **內容體積膨脹：** Phase 1 基底優化後 (2,728 篇)，Phase 2-3 以 5-8 篇/天新增 → 12 個月後預計總計 4,500-5,500 篇。爬蟲預算需重新配置（集中在 high-ROI pages）
- **首頁 link equity 變化：** 靜態首頁 + 5 分類 hub + pillar features → 首頁 link equity 分散到 150+ pillar pages（vs. 原 2,728 均勻分散）。預期提升 pillar page 排名 +3-5 位
- **內部連結網路複雜性：** hub-and-spoke topic cluster → O(n) 內部連結（vs. 原 sparse network）。爬蟲路徑最短距離 < 3 clicks，crawl efficiency 提升 2x
- **API Rate Limiting Cascade：** Phase 2-3 同時執行內容生成 + 發布 + 社群分發 → 潛在 WordPress.com API 瓶頸。需監控 429 errors，實施自適應延遲
- **GSC Re-evaluation 風險：** 短時間內新增 3,500+ 篇文章 + 全站 Schema 更新 → Google 可能觸發 re-evaluation。預期 2-4 週排名波動（見 Phase 1 learnings）
- **Helpful Content 政策風險：** AI 生成內容需通過品質閘門 (≥70/100) 且無重複檢測。需監控 Google Search Console > Security > Manual Actions，無有害內容標記

## Risks & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| WordPress.com API rate limit 在 Phase 2-3 達到瓶頸（併發發布 + 優化） | Med | High | 實施 adaptive delay (start 500ms, ↑ to 2s on 429)，監控 API error rate，必要時分散至不同時間 |
| AI 生成內容被 Google 標記為「對用戶有害」或違反 Helpful Content 政策 | Low | High | 100% 品質檢查 (≥70 score)，每月人工抽審 50 篇，監控 GSC 手動操作和流量異常 |
| 關鍵字研究 API 無免費層或額度不足 | Med | Med | 備選方案：Google Suggest 爬蟲（低成本）+ GSC existing queries（0 成本）；最壞情況下手動挑選 100+ 高機會關鍵字作為種子 |
| 首頁重構導致原有首頁排名喪失（新 URL 結構） | Low | Med | 設定 301 redirects 從舊首頁 → 新靜態首頁；在 GSC 提交 URL 變更；監控 14 天 re-indexation |
| 內部連結網路複雜度過高，導致 link juice 分散無法集中到 pillar pages | Low | Med | 定期審視 cluster 結構，確保 pillar page inbound links ≥ 10 per cluster；監控 pillar pages 的排名趨勢 |
| X API 成本隨發布量增加（$0.01/tweet，無免費方案） | Low | Low | 5-8 篇/天 ≈ $1.50-2.40/月，成本可控。優先使用免費的 Threads API 分攤；LINE 針對台灣訂閱者 |
| 發布節奏過快觸發 Google Helpful Content 偵測 | Med | High | 限制 5-8 篇/天（非 30-50），先 draft 再 scheduled publish，模擬自然發布模式 |
| 品質閘門評分標準不當，導致低品質內容通過且損害 SEO | Med | High | Phase 2 前期用 30% 黃色文章進行人工抽審，根據反饋調整評分權重；每月重新校準標準 |
| 5-8 篇/天的發布節奏數學上可能無法達到 10x（預估 4,500 篇 ≈ 6-7x） | Med | Med | Phase 1 優化存量 (3-4x) + 新文章長尾流量 + 社群放大器。若 Month 6 未達 6x，評估是否提升到 10-15 篇/天 |
| AI 生成來源引用為偽造 URL（模型幻覺） | Med | Med | 品質閘門 `fact-checker.js` 須對引用 URL 執行 HTTP HEAD 驗證（200 = pass, 404 = reject），不僅做 regex 匹配 |
| Tier 1 文章優化後排名下降（re-evaluation volatility）| Med | Med | 預期 7 天內排名 -3~5 位，14 天後恢復。在 GSC 設定告警：CTR ↓ 30% 或 impressions ↓ 40%，觸發人工檢查 |

## Documentation / Operational Notes

- **Phase 1 Go/No-Go Checkpoint (Day 14)：** 監控 CTR 改善 ≥ +15%、impressions 無明顯下降、無排名大幅波動。若任一指標未達，暫停 Phase 2，進行診斷
- **Phase 2 品質報告（每週）：** publish-queue.json + quality-scores.json 統計，黃色文章人工審稿率，平均品質分數趨勢
- **GSC 監控儀表板（每週一）：** 生成 performance-report.json，top winners/losers，CTR 變化，長尾關鍵字增長
- **API 成本追蹤（每日）：** 記錄 Claude API token 消耗（按 phase），Anthropic 月度發票預估
- **社群分發指標（每週）：** X followers growth、Threads engagement rate、LINE OA 訂閱數
- **Rollback Plan：** 若出現異常（e.g., Manual Action from Google），保留 state JSON checkpoints，可恢復至任意 checkpoint

## Phased Delivery

### Month 1-2: Phase 1 基底優化
- Week 1: Units 1.1-1.2（SEO optimization + homepage）
- Week 2: Units 1.3-1.4（schema + breadcrumbs）
- Week 3-4: Unit 1.5-1.6（internal links + tags）
- Week 5-8: GSC 監控 + 14-day GO/NO-GO checkpoint

**Exit criteria：** CTR +15%, no major ranking drops, Phase 1 report published

### Month 3-6: Phase 2 程式化擴張
- Week 1-2: Unit 2.1（keyword research）
- Week 3-4: Unit 2.2（content generation pilots）
- Week 5-6: Unit 2.3（quality gates calibration）
- Week 7-12: Unit 2.4-2.5（topic clusters + auto publishing）

**Parallel：** GSC monitoring, daily content output tracking

**Exit criteria：** 1,500+ articles generated and published (5-8/day sustainable), 80%+ pass quality gates, no SC4 violations

### Month 6-12: Phase 3 多渠道放大
- Week 1-2: Unit 3.1（social dispatch setup — Threads + X + LINE）
- Week 3-4: Unit 3.1 piloting + monitoring
- Week 5-24: Unit 3.2（analytics-driven iteration loop）+ 持續內容發布（5-8 篇/天）

**Parallel：** GSC/GA4 monitoring, social metrics dashboard

**Exit criteria：** 10x traffic achieved (342K+ monthly views), zero manual actions from Google, sustainable 5-8 articles/day output, social channels active

## Sources & References

**Origin document:**
- `docs/brainstorms/2026-04-08-10x-traffic-growth-requirements.md`

**Related plans:**
- `docs/plans/2026-04-08-002-feat-homepage-seo-architecture-plan.md` (Homepage design, Units 1.2-1.3)
- `docs/plans/2026-04-08-001-feat-tag-architecture-optimization-plan.md` (Tag strategy, Unit 1.6)
- `docs/plans/2026-03-31-seo-phase2-post-deployment-monitoring.md` (Phase 1 monitoring framework)

**Implementation scripts:**
- `scripts/yolo-lab-seo-optimizer-v3.js` (Core 4-dimension SEO)
- `scripts/batch-publisher.py` (WordPress API pattern)
- `scripts/bulk_tags_final.py` (Tag operations)

**Documentation:**
- `docs/YOLOLAB_QUICK_REFERENCE.md` (API reference)
- `docs/YOLOLAB_EXECUTION_GUIDE.md` (Phase-by-phase instructions)
- `docs/YOLOLAB_CHECKLIST.md` (GO/NO-GO gates)

**External references:**
- Google Search Console API documentation
- Google Analytics 4 API documentation
- Schema.org/WebSite, Article, SearchAction, CollectionPage
- [X API v2 pricing (2026)](https://docs.x.com/x-api/fundamentals/rate-limits) — $0.01/tweet pay-per-use
- [Threads API (Meta)](https://developers.facebook.com/docs/threads) — 免費，完全可用
- [LINE Messaging API](https://developers.line.biz/en/reference/messaging-api/) — Push 按量計費
- [DataForSEO API](https://dataforseo.com/pricing) — $0.0006/SERP request
- [Google AI Content Guidelines 2026](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content)
- `docs/batch1-2-humanization-report.md` — 29 個 AI 反模式清單

**Institutional learnings applied:**
- 29 AI 反模式清單嵌入內容生成 prompt（Learning #5）
- 已驗證的 rate limiting 配置：3 retries, 1.5-2s backoff, 0.5s inter-request（Learning #2）
- 14 天 GSC 檢查點（非 7 天）避免 re-evaluation 假警報（Learning #11）
- Pre-update backup pattern（Learning #3）
- Batch API vs Real-time 成本 33x 差距（Learning #10）
