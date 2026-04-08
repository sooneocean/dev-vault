---
title: "feat: YOLO LAB 首頁排版 × 站內連結 × SEO 骨架全面重構"
type: feat
status: active
date: 2026-04-08
origin: User request — "首頁排版切版格局 站內布局連結 SEO結構 一切由你安排"
---

# YOLO LAB 首頁排版 × 站內連結 × SEO 骨架全面重構

## Overview

將 yololab.net 從「無結構 blog roll 首頁」改造為**主題叢集入口**，並系統性建立：

1. **靜態首頁模板** — Hero + Category Hub Grid + Pillar Feature + Recent Posts
2. **5大分類頁 editorial content** — 各 150-250 字unique描述 + CollectionPage schema
3. **Homepage SEO schema** — WebSite + SearchAction + Organization @graph
4. **全站麵包屑系統** — BreadcrumbList JSON-LD via Yoast/template
5. **內部連結網絡腳本** — 批量為 Tier 1 文章建立 pillar → cluster 雙向連結

## Problem Frame

**現狀診斷（2026-04-08）：**

| 問題 | 狀態 | SEO 影響 |
|------|------|---------|
| 首頁 = blog roll，無靜態front page | ❌ | H1 混亂，link equity 分散 |
| 分類頁無editorial content | ❌ | Google 視薄頁面降權 |
| 零內部連結網絡 | ❌ | 1,695 孤立文章，crawl budget 浪費 |
| 無 WebSite+SearchAction Schema | ❌ | 損失 Sitelinks Search Box |
| 無麵包屑 BreadcrumbList | ❌ | SERP 顯示無結構資訊 |
| 無 Pillar Pages 架構 | ❌ | 無法建立主題權威 |

**目標：** 在 8 週後達成流量回升 +30%，Category pages organic traffic +50%，首頁 Lighthouse SEO ≥ 90。

## Requirements Trace

- R1. 首頁有唯一H1 + Hero section，category hub 用H2，文章標題用H3
- R2. 5個主要分類頁各有 150-250 字editorial content（unique，非重複）
- R3. Homepage 有完整 WebSite + SearchAction + Organization JSON-LD
- R4. 全站每頁有 BreadcrumbList schema（home → category → article）
- R5. 每篇 Tier 1 文章有 ≥3 個內部連結（含1個指向 pillar page）
- R6. 每個 category 有1個指定 pillar page，pillar page 有 ≥10 個 cluster 文章連結
- R7. 首頁→分類→文章點擊深度 ≤ 3 clicks

## Scope Boundaries

**In Scope:**
- 首頁靜態頁面建立（via wpcom-mcp pages.create）
- FSE 首頁 template block 結構設計（directional guidance）
- 5個主要分類的 editorial description 撰寫 + 更新
- Homepage SEO schema 腳本生成
- Pillar Page 指定（從現有文章選取，不新增內容）
- 內部連結批量腳本（Node.js，繼承 v3 optimizer 架構）

**Out of Scope:**
- 文章內容改寫（由 SEO batch optimizer 處理）
- Tag 架構（已在 2026-04-08-001 計畫中）
- 自定義 CSS/theme 主題修改
- 付費插件購買（Yoast Premium 等）
- 全站 Core Web Vitals 優化（獨立工作）

## Context & Research

### Existing Code Patterns

- `scripts/yolo-lab-seo-optimizer-v3.js` — Claude API + WordPress.com MCP 批量操作範本；state management, batchSize/delay/retry pattern，需延伸為內部連結模組
- `scripts/batch-publisher.py` — WordPress.com REST API v1.1，`meta[jetpack_seo_html_title]` + `meta[advanced_seo_description]` 更新 pattern
- `scripts/bulk_tags_final.py` — 分類ID映射表 + rate limiting pattern（可複用在分類描述更新）
- `docs/YOLOLAB_PHASE1_EXECUTION.md` — Tier 1 文章 ID 清單（IDs: 24748, 26777, 25243, 26646 等）
- `docs/YOLOLAB_QUICK_REFERENCE.md` — category slug/ID 對照表

### Current Site Architecture

```
yololab.net (現況)
├── 首頁：blog roll (query loop, 6-col CSS grid)
│   ├── Navigation: Home | 分類 | Search
│   └── No hero, no category hubs, no pillar links
├── /category/film/    (bare post grid, 無editorial content)
├── /category/music/   (bare post grid, 無editorial content)
├── /category/tech/    (bare post grid, 無editorial content)
├── /category/sports/  (bare post grid, 無editorial content)
└── /category/entertainment/  (bare post grid, 無editorial content)
```

### Target Architecture

```
yololab.net (目標)
├── 首頁 (static front page)
│   ├── [NAV] Home | Film | Music | Tech | Sports | Entertainment | Search
│   ├── [HERO] H1: 品牌聲明 + 150字品牌描述 + CTA
│   ├── [TRENDING] Tier 1 featured articles (3-4 cards)
│   ├── [CATEGORY HUBS] 5-col grid
│   │   ├── H2: Film → 3 latest + "See all" link
│   │   ├── H2: Music → 3 latest + "See all" link
│   │   ├── H2: Tech → 3 latest + "See all" link
│   │   ├── H2: Sports → 3 latest + "See all" link
│   │   └── H2: Entertainment → 3 latest + "See all" link
│   ├── [PILLAR FEATURE] 2 pillar pages prominently surfaced
│   └── [RECENT] 6-9 latest cross-category posts
├── /category/film/
│   ├── BreadcrumbList: Home > Film
│   ├── H1: Film (auto from query-title block)
│   ├── 150-250字 editorial intro (term-description block)
│   ├── Post grid (H2 per article title)
│   └── Related categories links
└── [repeat for Music/Tech/Sports/Entertainment]
```

### Heading Hierarchy Rules

| Page Type | H1 | H2 | H3 |
|-----------|----|----|-----|
| Homepage | Brand tagline (hero) | Category labels (Film, Music…) | Article titles within each hub |
| Category archive | Category name (query-title block) | Section labels (Latest, Featured) | Article titles in grid |
| Single article | Post title (auto) | Article sections | Subsections |

### Institutional Learnings

- Phase 1 plan (2026-04-03) confirms: internal linking network 完全缺失是流量暴跌主因之一
- Tag architecture plan (2026-04-08-001) has already designated 5-7 super-tag clusters that align with these 5 category hubs — cross-reference tag IDs when building category links

### External References

- WebSite + SearchAction Schema enables Google Sitelinks Search Box (schema.org/WebSite)
- CollectionPage Schema appropriate for category archives (schema.org/CollectionPage)
- Category pages need 150-250 word unique editorial content above post grid for Google E-E-A-T signals
- Hub-and-spoke: homepage → category hub (H2 block) → pillar page → cluster articles — 3 click max depth

## Key Technical Decisions

- **Static Front Page**: Create a blank WordPress Page titled "首頁" via `wpcom-mcp-content-authoring`, set as static front page. Do NOT use the blog roll as homepage. `/blog/` or `/archive/` becomes the posts page.
- **FSE Template Approach**: Use Site Editor block template for `front-page.html` — `cover` block for hero, `columns` block for category hubs, `query` block filtered by category ID per hub column.
- **Category Description Field**: Use WordPress's built-in category description field (Posts > Categories > Edit > Description) — surfaced automatically by FSE `term-description` block. No custom DB fields needed.
- **Schema Injection**: Homepage schema (@graph) injected via Yoast SEO > Schema tab (preferred) or `wp_head` hook via functions.php snippet if plugin unavailable on plan tier.
- **Internal Link Script**: Extend `scripts/yolo-lab-seo-optimizer-v3.js` with a new `--phase link` mode, separate from the SEO metadata phases, targeting Tier 1 articles first.
- **Breadcrumbs**: Use Yoast SEO breadcrumb block in FSE templates (available on WordPress.com Business plan). If unavailable, inject BreadcrumbList JSON-LD per-template via `wp_head` hook for single posts and category archives.
- **Pillar Pages**: Selected from existing Tier 1 articles with highest views — no new content creation required. 1 pillar per category = 5 total pillar pages.

## Open Questions

### Resolved During Planning

- **Q: WordPress.com plan tier?** Assumed Business plan (plugin support). If Personal/Premium tier, Yoast plugin unavailable — fallback to meta box or MCP-injected schema per article.
- **Q: 分類頁 H1 auto-generation?** FSE `core/query-title {"type":"archive"}` block auto-generates H1 from the category name. No manual override needed per category.
- **Q: 首頁 H1 content?** Brand-level tagline: "YOLO LAB｜解構科技邊際與媒體娛樂的數據實驗室" — matches existing brand identity ("撕開平庸媒體的假面"), keyword-rich, not an article title.
- **Q: Pillar page selection source?** From `docs/YOLOLAB_PHASE1_EXECUTION.md` Tier 1 list — highest-view articles per category. 5 total (one per category).

### Deferred to Implementation

- Exact category IDs from WordPress for use in Query Loop `categoryIds` parameter — confirm via MCP `categories.list` during execution
- Exact article IDs for the 5 pillar pages — confirm against GSC top performers during execution
- Whether Yoast SEO plugin is installed and active on the WordPress.com plan — test via site editor during execution

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

### Homepage Template Block Flow

```
[template-part: header]
  └── nav: Home | Film | Music | Tech | Sports | Entertainment | 🔍

[Cover block — HERO, full-width, align:full]
  └── Heading H1: "YOLO LAB｜解構科技邊際與媒體娛樂的數據實驗室"
  └── Paragraph: brand description (150 words)
  └── Buttons: "瀏覽分類" → /category/film/, "最新文章" → /blog/

[Group block — TRENDING]
  └── Heading H2: "熱門精選"
  └── Query Loop (perPage:4, orderBy:comment_count or manual IDs)
      └── Post Template: featured-image + post-terms + post-title H3

[Columns block — CATEGORY HUBS, 5 columns desktop / stacked mobile]
  ├── Column: Heading H2 "Film" (linked to /category/film/)
  │           Query Loop (perPage:3, categoryIds:[FILM_ID])
  │             └── Post Template: featured-image + post-title H3
  │           Button: "所有電影文章 →"
  ├── Column: Heading H2 "Music" ... [repeat pattern]
  ├── Column: Heading H2 "Tech"  ...
  ├── Column: Heading H2 "Sports" ...
  └── Column: Heading H2 "Entertainment" ...

[Group block — PILLAR FEATURE]
  └── Heading H2: "深度長文"
  └── Columns (2-col): each pillar page as card
      └── featured-image + post-excerpt (numberOfWords:40) + H3 title

[Query Loop — RECENT POSTS, 9 posts, cross-category]
  └── Heading H2: "最新發布"
  └── Post Template (grid, columnCount:3): featured-image + post-title H3 + post-date

[template-part: footer]
  └── footer-nav: category links (Film|Music|Tech|Sports|Entertainment)
  └── copyright + logo
```

### Homepage Schema @graph

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://yololab.net/#website",
      "url": "https://yololab.net/",
      "name": "YOLO LAB",
      "description": "解構科技邊際與媒體娛樂的數據實驗室",
      "inLanguage": "zh-TW",
      "potentialAction": {
        "@type": "SearchAction",
        "target": { "@type": "EntryPoint", "urlTemplate": "https://yololab.net/?s={search_term_string}" },
        "query-input": "required name=search_term_string"
      }
    },
    {
      "@type": "Organization",
      "@id": "https://yololab.net/#organization",
      "name": "YOLO LAB",
      "url": "https://yololab.net/",
      "logo": { "@type": "ImageObject", "url": "https://yololab.net/logo.png" }
    },
    {
      "@type": "WebPage",
      "@id": "https://yololab.net/#webpage",
      "url": "https://yololab.net/",
      "name": "YOLO LAB — 首頁",
      "isPartOf": { "@id": "https://yololab.net/#website" }
    }
  ]
}
```

### Internal Link Script Architecture

```
scripts/internal-linker.js
  --phase audit    → crawl all Tier1 articles, count incoming/outgoing internal links, output JSON
  --phase add      → for each Tier1 article, inject 3+ links (1 pillar + 2 cluster peers) via posts.update
  --pillar-map     → reads pillar-map.json (category → pillar article ID)
  --tier 1|2|3     → article tier filter (default: Tier 1 first)
  --dry-run        → preview changes without API calls
  --resume <date>  → resume interrupted batch
```

## Implementation Units

- [ ] **Unit 1: 靜態首頁頁面建立**

**Goal:** 在 WordPress 中建立靜態「首頁」Page，設定為 Front Page，並設計完整的 FSE block 結構。

**Requirements:** R1, R7

**Dependencies:** None

**Files:**
- Create: `scripts/homepage-builder.js` — 使用 wpcom-mcp-content-authoring pages.create 建立首頁，注入完整 FSE block markup
- Modify: (WordPress Settings > Reading 設定 static front page — 透過 MCP 或 WP admin)

**Approach:**
- 使用 `wpcom-mcp-content-authoring` (pages.create) 建立 title="首頁" 的靜態 Page
- Page content 為完整 FSE block HTML（Cover hero + Columns category hubs + Query loops + Pillar feature）
- Category hub 的 Query Loop 用 `{"inherit":false,"perPage":3,"categoryIds":[ID]}` — 每個 column 對應一個分類ID
- Hero block 使用現有 dark theme (#050811) + 黃色 accent (#ffffa0) 配色，保持品牌一致性
- 執行後透過 wpcom-mcp 取得 edit link + preview link

**Patterns to follow:**
- `scripts/batch-publisher.py` WordPress.com REST API v1.1 的 page creation pattern
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 batchSize/delay/retry + state management pattern

**Test scenarios:**
- Happy path: Page 建立成功，返回 page ID 和 edit URL
- Edge case: 已存在同名頁面時不重複建立（先 GET 確認）
- Integration: 建立後 WordPress Settings > Reading 正確顯示為 Front Page
- Verification: WebFetch yololab.net 確認 H1 存在於 hero section，分類 hub H2 × 5 出現在頁面

**Verification:**
- `curl https://yololab.net | grep '<h1'` 只出現1次
- 分類 hub 可見5個 H2 (Film/Music/Tech/Sports/Entertainment)
- 首頁 → 任意文章 ≤ 3 clicks

---

- [ ] **Unit 2: 分類頁面 Editorial Content 撰寫與部署**

**Goal:** 為 Film/Music/Tech/Sports/Entertainment 5個分類各寫 150-250 字的獨特editorial description，並部署至 WordPress category description 欄位，同時更新 meta title/description。

**Requirements:** R2

**Dependencies:** None (parallel with Unit 1)

**Files:**
- Create: `scripts/category-content-updater.js` — 使用 Claude API 生成5個分類 editorial descriptions，透過 wpcom-mcp 更新 taxonomies
- Create: `data/category-descriptions.json` — 生成的分類描述暫存

**Approach:**
- 用 Claude API (haiku-4-5) 為每個分類生成：
  - editorial description (150-250字，繁體中文，含主要關鍵詞)
  - meta title (格式：`[分類名] — YOLO LAB | [關鍵詞短語]`，≤60 chars)
  - meta description (≤160 chars，描述性，含CTA)
- 透過 `wpcom-mcp-content-authoring` taxonomies.update 寫入 category description
- 透過 Yoast SEO meta box 或 Jetpack SEO meta 更新 meta title/description per category

**Category description prompts (directional — 每個分類需要獨特切角):**
- Film: 電影評論、院線新片、串流平台推薦、導演分析視角
- Music: 新專輯評論、藝人動態、音樂產業解析、華語/韓語/歐美跨域
- Tech: 科技產業趨勢、AI工具評測、消費電子、數位政策
- Sports: 職業賽事分析、運動員人物誌、體育產業數據
- Entertainment: 影視綜合、明星動態、文化評論、娛樂產業觀察

**Patterns to follow:**
- `scripts/bulk_tags_final.py` 的 category ID → API update pattern
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 Claude API prompt pattern

**Test scenarios:**
- Happy path: 5個分類description各自unique，150-250 字，無重複段落
- Edge case: Category ID不存在時有明確錯誤訊息
- Integration: 更新後 `/category/film/` 的 `term-description` block 可見新內容
- Verification: 5個分類頁 WebFetch，確認editorial content 在 H1 之後、文章grid之前出現

**Verification:**
- `WebFetch /category/film/` 首屏可見150+字editorial content
- 5個分類 meta description 皆 ≤160 chars（用 curl -I 或 WebFetch確認）
- Google Rich Results Test 對 category pages 無結構錯誤

---

- [ ] **Unit 3: Homepage SEO Schema 部署**

**Goal:** 為首頁部署完整的 WebSite + SearchAction + Organization + WebPage JSON-LD @graph，啟用 Google Sitelinks Search Box 潛力。

**Requirements:** R3

**Dependencies:** Unit 1（首頁靜態頁面需先存在）

**Files:**
- Create: `scripts/schema-homepage-injector.js` — 生成homepage schema JSON-LD，透過 Yoast SEO 或 WP options API 注入
- Create: `data/homepage-schema.json` — schema 模板

**Approach:**
- 優先嘗試透過 Yoast SEO REST API 設定 homepage schema（WordPress.com Business plan 有Yoast）
- 若 Yoast API 不可用：透過 wpcom-mcp posts.update 把 `<!-- schema -->` 區塊注入首頁 Page content 的 Custom HTML block
- Schema content 見 High-Level Technical Design 的 @graph 設計
- 驗證：使用 Google Rich Results Test URL

**Patterns to follow:**
- `docs/YOLOLAB_QUICK_REFERENCE.md` Schema type decision matrix
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 schema generation pattern

**Test scenarios:**
- Happy path: 首頁 `<head>` 中出現 `@type: WebSite` + `@type: Organization` + SearchAction
- Edge case: 避免與 Yoast 已自動生成的 schema 重複 — 若 Yoast 已有WebSite schema，僅補充 SearchAction potentialAction
- Integration: Google Rich Results Test `https://yololab.net` 通過 WebSite 測試
- Verification: `curl https://yololab.net | grep 'SearchAction'` 有輸出

**Verification:**
- Google Rich Results Test 首頁通過 (WebSite type)
- Schema Markup Validator 無 error（warning 可接受）
- 若有 Sitelinks Search Box：Google 搜尋 "yololab" 出現搜尋框

---

- [ ] **Unit 4: 全站麵包屑 BreadcrumbList 系統**

**Goal:** 為 single post 和 category archive 兩種 page type 建立 BreadcrumbList JSON-LD，改善 SERP 顯示和 Google 理解站內結構。

**Requirements:** R4, R7

**Dependencies:** Unit 1（首頁URL確認後）

**Files:**
- Modify: WordPress Site Editor — single.html template part (加 breadcrumb block)
- Modify: WordPress Site Editor — category.html template part (加 breadcrumb block)
- Create: `scripts/breadcrumb-schema-validator.js` — 對代表性頁面批量驗證 BreadcrumbList

**Approach:**
- 首選：在 FSE Site Editor 的 single post template 加入 `wp:yoast-seo/breadcrumbs` block（Yoast available）
- 次選：若 Yoast 不可用，在 single post template 加入 `wp:rank-math/breadcrumb` block
- 後備方案：透過 Custom HTML block 在 post content 頭部注入 BreadcrumbList JSON-LD
- 麵包屑路徑：`Home > [Category] > [Article Title]`（single posts）；`Home > [Category]`（category archives）
- 在 Site Editor 操作透過 `wpcom-mcp-site-editor-context` 確認 theme 支援的 block 列表

**Patterns to follow:**
- 現有 site 已有 CollectionPage + Organization schema — breadcrumb 是補充，不替換
- `docs/plans/2026-04-04-unit1-2-schema-deployment-plan.md` 的 Yoast SEO configuration pattern

**Test scenarios:**
- Happy path: 隨機抽 5 篇文章，`<head>` 含 BreadcrumbList，trail 正確（Home → Category → Article）
- Edge case: 文章屬於多分類時，breadcrumb 使用 primary category（Yoast 設定）
- Integration: Google SERP 測試（14天後確認 breadcrumb 在搜尋結果顯示）
- Verification: Rich Results Test 對 5 篇文章 + 5 個分類頁面全部通過 BreadcrumbList

**Verification:**
- `scripts/breadcrumb-schema-validator.js --sample 10` 通過率 ≥ 90%
- Single post template 在 Site Editor 可見 breadcrumb block

---

- [ ] **Unit 5: Pillar Page 指定 + 內部連結批量腳本**

**Goal:** 從 Tier 1 文章清單中每個分類各選定 1 篇 Pillar Page，建立 pillar-map.json，並實作 `scripts/internal-linker.js` 批量腳本，為 Tier 1 文章注入內部連結（≥3條/篇，含1條→pillar）。

**Requirements:** R5, R6

**Dependencies:** Unit 1 + Unit 2（分類架構確認後）

**Files:**
- Create: `data/pillar-map.json` — {category_slug: pillar_post_id} 映射
- Create: `scripts/internal-linker.js` — 批量內部連結注入腳本
- Create: `data/link-audit-results.json` — 執行後輸出：每篇文章的 incoming/outgoing link 計數

**Approach:**

**Pillar Page 選定標準：**
- 從 `docs/YOLOLAB_PHASE1_EXECUTION.md` Tier 1 清單中，每個分類選 views 最高的 1 篇
- Pillar page 理想特徵：字數 ≥ 1,500，覆蓋分類的核心主題，非時效性內容
- 初始 pillar candidates（待執行時確認 view counts）：
  - Film: 從 IDs 24748, 26777 中選
  - Music: 從 IDs 25243, 26646 中選
  - Tech/Sports/Entertainment: 同 Tier 1 清單

**internal-linker.js 架構：**
- `--phase audit` — 抓 Tier 1 文章列表，統計 outgoing internal links（解析 post_content HTML），輸出 link-audit-results.json
- `--phase add` — 讀 pillar-map.json，對每篇 Tier 1 文章 (perBatch:10, delay:1000ms)：
  1. GET 原文章 content
  2. 用 Claude API 找語義相關段落，建議插入位置（避免破壞現有格式）
  3. 插入 3 條內部連結：1條→pillar，2條→同分類 cluster peers
  4. `posts.update` 寫回
- `--dry-run` — 輸出 proposed-links.json 供人工確認，不執行更新
- State management：繼承 v3 optimizer 的 `state_link_tier{N}.json` 格式

**連結規則（硬性限制）：**
- anchor text：描述性 partial-match（不使用「點這裡」「閱讀更多」「here」）
- 每篇文章 outgoing internal links ≤ 8
- Pillar-pointing link 置於文章前1/3內（第一或第二段落附近）
- 跨分類連結比例 ≤ 30%（保持主題叢集聚焦）

**Patterns to follow:**
- `scripts/yolo-lab-seo-optimizer-v3.js` 的 state JSON、retry logic、`--dry-run`、`--resume` flags
- `scripts/batch-publisher.py` 的 `posts.update` API pattern

**Test scenarios:**
- Happy path (audit phase): 輸出 link-audit-results.json，Tier 1 50篇全部有 outgoing/incoming 統計
- Happy path (add phase --dry-run): proposed-links.json 中每篇 ≥ 3 個新連結，anchor text 非空、非「here」
- Edge case: 文章已有 ≥ 8 internal links → skip，記錄至 skipped.json
- Edge case: Pillar page 本身不插入指向自身的連結
- Error path: API 429 rate limit → exponential backoff，最多 3 retries
- Integration: add phase 執行後，抽驗 5 篇文章，posts.update 回應 200，content 包含新 `<a href="/...">` 標籤

**Verification:**
- `--phase audit` 完成後 link-audit-results.json 可讀
- `--dry-run` 完成後 proposed-links.json 每筆有 `{postId, anchorText, targetUrl, insertionContext}`
- 人工確認 proposed-links.json 後，`--phase add --tier 1` 執行，更新率 ≥ 95%

---

- [ ] **Unit 6: Navigation Menu 結構優化**

**Goal:** 確保首頁導覽選單包含5大分類的直達連結，footer 有 sitemap 型連結區，確保 homepage → category ≤ 1 click。

**Requirements:** R7

**Dependencies:** Unit 1

**Files:**
- (WordPress admin) Appearance > Menus — 更新主導覽選單
- (WordPress admin) Widgets / Footer template — 加入 Category Links group

**Approach:**
- 主導覽：`Home | Film | Music | Tech | Sports | Entertainment | 🔍 Search`
- 每個分類名直接連結到 `/category/[slug]/`（不用下拉選單，保持單層扁平）
- Footer：加入「分類」區塊，列出 5 大分類 + 熱門 tag 連結
- Footer 左欄：About/Contact/Privacy；Footer 右欄：Categories + Tags
- 透過 `wpcom-mcp-site-editor-context` 確認現有 navigation block 結構，對應修改

**Patterns to follow:**
- 現有 site 已有 responsive navigation with hamburger toggle — 保持行動端兼容

**Test scenarios:**
- Happy path: 首頁 Desktop nav 顯示所有5個分類連結
- Happy path: Footer 有 Film/Music/Tech/Sports/Entertainment 超連結
- Integration: 手機寬度（375px）下 hamburger 選單展開後分類可見
- Verification: WebFetch yololab.net，HTML 中 `<nav>` 包含5個分類 href

**Verification:**
- nav bar 上可見 Film/Music/Tech/Sports/Entertainment
- footer category 連結可用（200 response）
- 無 broken links（404）在 nav

## System-Wide Impact

- **Interaction graph:** 靜態首頁建立後，WordPress `query_posts_per_page` 設定不再影響首頁 — 由 FSE 的各 Query Loop 各自控制 `perPage`
- **Error propagation:** Category ID 設定錯誤的 Query Loop block → 顯示空白欄位（不 crash），但需在建立後人工核驗5個 category hub 欄位有資料
- **State lifecycle risks:** Unit 5 的 posts.update 若失敗 mid-batch，state JSON 確保 resume 不重複寫入
- **API surface parity:** 內部連結腳本使用 WordPress.com REST API v1.1 (同 batch-publisher.py)，速率限制 10 req/s → batchSize:10 + delay:1000ms 是安全值
- **Unchanged invariants:** 現有文章的 Yoast SEO meta title/description（Unit 1-2 of 2026-04-03 plan 已完成）不被本計畫覆蓋 — internal-linker.js 只修改 post_content，不改 SEO meta
- **Integration coverage:** 首頁 Query Loop 對各分類的文章抓取是動態的 — 新文章發布後自動出現在對應 hub，無需手動更新

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| WordPress.com 方案限制（未到 Business plan）→ Yoast 插件不可用 | 後備方案：Custom HTML block 注入 schema；BreadcrumbList 用 JSON-LD per-template |
| Category IDs 在 FSE Query Loop 需硬編碼 → 分類ID未知 | 執行時先 `wpcom-mcp-content-authoring categories.list` 取得完整ID表 |
| 首頁 static page 設定後，舊 blog roll 首頁消失 → /blog/ 或 /archive/ 需同時建立 | 建立靜態首頁前，先建立 /blog/ page 作為 posts page |
| internal-linker.js 可能破壞現有 block editor 格式（HTML → Gutenberg blocks 結構） | --dry-run 先人工確認5篇測試文章；優先用 `paragraph` 型文章（非複雜 block 結構）開始 |
| 分類 editorial content 如果被 Google 認為重複（各分類文字太相似）| 每個分類 description 由獨立 Claude prompt 生成，明確要求「與其他分類描述完全不重複視角」 |
| 流量回升需時 — 8週內 +30% 非保證 | 設定 GSC 14天 GO/NO-GO checkpoint（沿用 2026-04-03 plan 的 monitoring 框架） |

## Documentation / Operational Notes

- 首頁建立後：提供 WordPress admin edit link + preview link（via wpcom-mcp response）
- pillar-map.json 建立後加入 git，作為長期內容架構文件
- 內部連結執行前必須先跑 `--dry-run` 並人工確認 proposed-links.json
- 監控：沿用 `docs/YOLOLAB_CHECKLIST.md` 的 GO/NO-GO checkpoint 架構；在 Unit 5 完成後14天加設「內部連結效果」監控點（GSC impressions for Tier 1 articles）

## Sources & References

- Related plans: `docs/plans/2026-04-03-seo-phase1-plan.md`, `docs/plans/2026-04-08-001-feat-tag-architecture-optimization-plan.md`
- Related code: `scripts/yolo-lab-seo-optimizer-v3.js`, `scripts/batch-publisher.py`, `scripts/bulk_tags_final.py`
- Data: `docs/YOLOLAB_PHASE1_EXECUTION.md` (Tier 1 IDs), `docs/YOLOLAB_QUICK_REFERENCE.md` (category reference)
- External: Schema.org/WebSite, Schema.org/SearchAction, Schema.org/CollectionPage
- Research: hub-and-spoke topic cluster model (2026 SEO best practices), FSE template hierarchy (front-page.html priority)
