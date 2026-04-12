---
title: "feat: YOLO LAB 圖片 Alt Text 自動化優化"
type: feat
status: completed
date: 2026-04-10
origin: docs/brainstorms/2026-04-08-10x-traffic-growth-requirements.md
deepened: 2026-04-12
confidence: 8.2/10
implementation_date: 2026-04-12
---

# feat: YOLO LAB 圖片 Alt Text 自動化優化

## Overview

為 YOLO LAB (yololab.net) 全站 2,728+ 篇文章的圖片自動生成 SEO 優化的 alt text，利用 Claude Vision 模型分析圖片內容，批次更新 WordPress.com 媒體庫。目標是解鎖 Google 圖片搜尋流量（潛在佔總流量 20-30%）並提升無障礙合規性。

## Problem Frame

YOLO LAB 目前月瀏覽量 34,270，70%+ 來自 Google 有機搜尋。全站 2,728+ 篇文章的圖片 alt text 幾乎為空或僅為檔名（如 `IMG_2034`），導致：

1. **Google 圖片搜尋流量為零**——無 alt text 意味著 Google 無法索引圖片內容
2. **AI 搜尋引擎無法引用圖片相關內容**——缺乏結構化描述
3. **WCAG 2.1 無障礙不合規**——所有非裝飾性圖片須有替代文字
4. **Google Discover 呈現受限**——缺乏描述性 alt text 影響內容卡片品質

歷史上僅 68 篇文章的 `featured_media` alt text 被手動更新過（2026-03-31 journal 記錄），其餘均未處理。

## Requirements Trace

- R1. 掃描全站文章，識別所有缺少 alt text 或 alt text 為檔名的圖片（featured_media + 文章內嵌圖片）
- R2. 使用 Claude Vision 模型分析圖片內容，生成 80-125 字元的繁體中文 alt text
- R3. Alt text 須自然融入 1-2 個與文章主題相關的長尾關鍵字
- R4. 批次更新 WordPress.com 媒體庫的 `alt` 欄位
- R5. 處理文章 HTML 中 `<img>` 標籤的 `alt` 屬性（內嵌圖片）
- R6. 產出品質驗證報告（更新數量、長度分布、失敗項目）
- R7. 支援可恢復的批次處理（斷點續傳）
- R8. 預更新備份，支援回滾

## Scope Boundaries

- **不含**圖片壓縮、格式轉換或 CDN 優化
- **不含**新圖片上傳或圖片替換
- **不含**影片/音訊媒體的描述
- **不含**英文或其他語言版本
- **不含**ImageObject Schema 注入（可作為後續迭代）
- **專注**：alt text 生成與更新，最大化圖片搜尋流量

## Context & Research

### Relevant Code and Patterns

- `scripts/wp-seo-batch-v3.js` — 生產級批次 SEO 腳本，Queue 類別、2 並行、100ms 延遲、checkpoint every 100 posts
- `scripts/internal-linker-v2.js` — 最成熟的 REST API 模式，retry/backoff、429 偵測、雙認證支援
- `scripts/yolo-lab-geo-optimizer-v1.js` — Claude tool_use 結構化輸出模式（最可靠的 JSON 提取方式）
- `scripts/phase4-complete-seo-batch-generator.js` — 全語料分頁取得模式（2,725 篇）

### Institutional Learnings

- **v1.1 vs v2 API 欄位差異**：v1.1 媒體更新用 `alt` 欄位；v2 用 `alt_text`。本專案使用 v1.1（see `phase4-complete-seo-batch-generator.js`）
- **保守速率限制有效**：batch size 5、delay 2000ms 在 Phase 9 的 posts 更新達成 100% 成功率（see `docs/PHASE9-12-SEO-EXECUTION-REPORT.md`）。media endpoint 的 rate limit 未經驗證，Unit 1 將先以小量測試確認
- **必須預備份**：所有批次更新前存 JSON 快照，配合 restore 腳本（see `docs/PLAN_REMEDIATION_GUIDE_2026-04-08.md`）
- **合併重複腳本**：避免建立多個相似腳本，應參數化設計（同一份 remediation guide 的教訓）
- **checkpoint 語義**：state 檔案在每批（5 項）處理後存檔。已處理項目（在 `processed` 陣列中）不重複處理；失敗項目以相同 payload 重試。內嵌圖片階段額外支援 `partial` 狀態——文章已更新但部分圖片未處理，resume 時僅重新處理未完成的圖片

### External References

- Google Search Central：alt text 是圖片搜尋排名的主要文字信號
- WordPress.com REST API v1.1：`POST /sites/{site_id}/media/{media_id}` 以 `alt` 欄位更新
- WCAG 2.1 Level A (1.1.1)：所有非裝飾性圖片須有替代文字
- 業界共識（web.dev、Moz、Ahrefs）：alt text 最佳長度 80-125 字元

## Key Technical Decisions

- **使用 Claude Vision（非純文字推測）**：直接分析圖片內容產生準確描述，而非僅靠文章標題猜測。雖然成本較高（需傳送圖片 token），但準確性顯著提升，避免「alt text 與圖片不符」的 Google 懲罰風險
- **混合 API 版本**：媒體 alt 更新用 REST API v1.1（`POST /media/{id}`, `alt` 欄位）；文章 content 讀寫用 wp/v2（`GET/POST /wp/v2/sites/{id}/posts/{id}?context=edit`）以取得包含 Gutenberg block comments 的 raw HTML，避免 rendered HTML 回寫破壞 block 結構。此模式已在 `internal-linker-v2.js` 中驗證
- **繁體中文 alt text**：YOLO LAB 是繁體中文站，alt text 以繁體中文生成，符合目標受眾搜尋行為
- **先處理 featured_media，再處理內嵌圖片**：featured_media 是媒體庫物件（API 直接更新），內嵌圖片需修改文章 HTML（風險較高），分兩階段降低風險。這是操作偏好而非硬性技術依賴——兩階段技術上可獨立執行
- **模型選擇 claude-haiku-4-5-20251001**：alt text 是短文本生成任務（80-125 字元），Haiku 足夠且成本最低（~$0.001/張圖片），2,728 篇文章預估 $3-5
- **圖片 URL 去重快取**：同一張圖片 URL 可能出現在多篇文章中，建立 `{ imageUrl: generatedAlt }` 快取，同一 URL 只呼叫 Claude Vision 一次，節省 API 成本並確保一致性。快取持久化到 state 檔案以支援 resume
- **Claude Vision 圖片傳遞方式**：優先嘗試 URL 模式（`source.type: "url"`），在 Unit 1 掃描階段用 1-2 張圖片驗證 `i0.wp.com` CDN 可存取性。若失敗則降級為 base64 模式（先下載再編碼）

## Deepening Improvements (2026-04-12)

從架構和可靠性審視發現 7 項關鍵改進，已整合至以下實施單位：

| # | 改進 | 相關 Unit | 優先級 | 改動類型 |
|----|------|----------|--------|--------|
| 1 | 內嵌圖片冪等性追蹤（URL 鍵 + 粒度化 state） | Unit 2, 4 | **HIGH** | 設計強化 |
| 2 | 認證前置健檢（開啟時驗証 API 可存取） | Unit 1 | **HIGH** | 新增檢查點 |
| 3 | 並發互斥鎖（檔案鎖防止衝突） | Unit 1 | **HIGH** | 新增機制 |
| 4 | API 超時保護（30-60 秒超時） | Unit 2, 3, 4 | **HIGH** | 錯誤處理強化 |
| 5 | 指數退避重試（3 次 + 速率限制檢測） | Unit 2, 3, 4 | **MEDIUM** | 錯誤恢復 |
| 6 | 執行後驗証（更新後 re-fetch 並比對） | Unit 3, 4 | **MEDIUM** | 驗証邏輯 |
| 7 | 回滾順序明確化（內嵌→featured 倒序） | Unit 5 | **MEDIUM** | 文檔 + 實裝 |

**信心度提升**：6.8 → 8.2/10 （20% 風險化解）

## Open Questions

### Resolved During Planning

- **WordPress.com 媒體 API 欄位名稱**：v1.1 用 `alt`，v2 用 `alt_text`。本腳本統一使用 v1.1 的 `alt`
- **Vision model 可否存取 WordPress 圖片 URL**：WordPress.com 圖片為公開 URL（`i0.wp.com` CDN），Claude Vision 可通過 URL 存取
- **已更新的 68 篇是否跳過**：是，腳本自動偵測已有合理 alt text 的項目並跳過

### Deferred to Implementation

- **部分圖片可能被 CDN 封鎖或 URL 失效**：需在實作時加入 URL 可存取性檢查，失敗項目記錄到 state
- **內嵌圖片的 HTML 解析**：使用正則匹配 `<img[^>]*>` 提取標籤，保留 Gutenberg block comments 不動。wp/v2 API 的 `context=edit` 回傳 raw HTML（含 `<!-- wp:image -->`），回寫時保持原始結構。若正則匹配異常則跳過該文章
- **每篇文章內嵌圖片數量分布**：需在 Phase 1 掃描時統計，影響 Phase 2 的成本估算
- **裝飾性圖片判斷**：Claude Vision 的 tool schema 包含 `is_decorative: boolean`，裝飾性圖片（spacer、分隔線、純背景）保持 `alt=""`，不填入描述性文字（符合 WCAG 2.1）
- **內嵌圖片部分失敗策略**：一篇文章有多張圖片時，若部分生成失敗，仍更新成功的圖片。State 中記錄該文章為 `partial`，resume 時重新處理未完成的圖片

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```mermaid
flowchart TD
    A[Phase 1: 掃描與盤點] --> B{圖片有 alt text?}
    B -->|空/檔名| C[加入待處理佇列]
    B -->|已有合理描述| D[跳過]
    C --> E[Phase 2: Claude Vision 分析圖片]
    E --> F[生成 80-125 字元繁體中文 alt text]
    F --> G{品質檢查}
    G -->|通過| H[Phase 3: WordPress API 更新]
    G -->|失敗| I[重試/人工標記]
    H --> J[Phase 4: 驗證報告]

    subgraph 兩類圖片
        M1[featured_media → API 更新 media/{id}]
        M2[內嵌 img → 修改 post HTML]
    end
```

**處理流程：**

1. **掃描階段**：wp/v2 API (`context=edit`) 分頁取得所有文章的 `featured_media` ID 和 `content.raw`，解析 `<img>` 標籤。附帶驗證 Vision URL 存取和 media API 更新行為
2. **過濾階段**：識別 alt 為空、為檔名、或過短（<10 字元）的圖片；去重相同 URL
3. **生成階段**：將圖片 URL + 文章標題 + 分類發送給 Claude Vision，生成 alt text。URL 去重快取避免重複呼叫
4. **更新階段**：featured_media 透過 v1.1 `POST /media/{id}` 更新 `alt`；內嵌圖片透過 wp/v2 `POST /posts/{id}` 更新 `content.raw`
5. **驗證階段**：重新取得更新後的資料，確認 alt text 已正確寫入

## Implementation Units

- [ ] **Unit 1: 全站圖片掃描與盤點腳本**

**Goal:** 掃描全站文章，產出圖片盤點報告（哪些圖片缺少 alt text、哪些已有）

**Requirements:** R1

**Dependencies:** None

**Files:**
- Create: `scripts/image-alt-text-optimizer.js`
- Output: `seo-optimization-output/image-audit-report.json`

**Approach:**
- **前置：並發鎖 + 認證檢查**（Deepening #2, #3）
  - 啟動時獲取排他檔案鎖 `seo-optimization-output/.batch.lock`，避免與其他 batch 腳本衝突
  - 驗証 WordPress.com API 認證、媒體讀寫權限、文章讀寫權限，若失敗則提前退出
- 複用 `phase4-complete-seo-batch-generator.js` 的分頁取得模式
- 使用 wp/v2 API（`context=edit`）取得每篇文章的 `id`, `title`, `featured_media`, `content.raw`, `categories`
- 對 `featured_media > 0` 的文章，呼叫 v1.1 `GET /media/{media_id}` 取得現有 `alt`
- 解析 `content.raw` 中的 `<img>` 標籤，提取 `src` 和 `alt` 屬性
- 分類統計：空 alt、檔名 alt（匹配 `IMG_\d+`, `DSC_\d+`, `Screenshot` 等模式）、合理 alt、刻意空 alt（潛在裝飾性圖片，標記為待 Vision 確認）
- 附帶驗證：用 1-2 張圖片 URL 測試 Claude Vision 的 URL 模式可存取性，結果記錄在報告中
- 同時驗證 v1.1 `POST /media/{id}` 更新 `alt` 欄位的行為（用一張測試圖片，測試後立即回滾）
- 產出 JSON 報告含全站圖片統計摘要和逐篇明細

**Patterns to follow:**
- `scripts/phase4-complete-seo-batch-generator.js` — 分頁取得全語料
- `scripts/internal-linker-v2.js` — REST API 認證與 rate limiting

**Test scenarios:**
- Happy path: 掃描 10 篇文章，正確識別 featured_media 和內嵌圖片的 alt 狀態
- Edge case: 文章無 featured_media（`featured_media: 0`）→ 跳過
- Edge case: 內嵌圖片無 `alt` 屬性 vs `alt=""` vs `alt="IMG_2034"` → 分別歸類
- Edge case: 文章 content 含 Gutenberg block comments `<!-- wp:image -->` → 正確解析
- Error path: API 回傳 429 → 指數退避重試

**Verification:**
- 產出的 `image-audit-report.json` 包含全站圖片統計摘要和逐篇明細
- 可在 `--sample 10` 模式下快速驗證正確性

---

- [ ] **Unit 2: Claude Vision Alt Text 生成引擎**

**Goal:** 使用 Claude Vision 分析圖片並生成 SEO 優化的繁體中文 alt text

**Requirements:** R2, R3

**Dependencies:** Unit 1（需要盤點報告作為輸入）

**Files:**
- Modify: `scripts/image-alt-text-optimizer.js`

**Approach:**
- **API 可靠性強化**（Deepening #4, #5）
  - 所有 Claude Vision 調用設 45 秒超時（AbortController），超時視為失敗並記錄，降級到純文字推測模式
  - 實施指數退避重試：3 次嘗試，延遲 1s, 2s, 4s（+隨機抖動），速率限制檢測時自動延長延遲
  - 失敗項統計與分類（API 失敗 vs 超時 vs Vision 拒絕），便於後續分析
- 使用 Claude tool_use 模式（參考 `geo-optimizer-v1.js`）確保結構化輸出
- 定義 `ALT_TEXT_TOOL` schema：`{ alt_text: string, is_decorative: boolean }`（精簡設計——關鍵字應自然融入 alt_text 本身，不需額外欄位；裝飾性圖片偵測避免 WCAG 違規）
- System prompt 指示：繁體中文、80-125 字元、自然融入關鍵字、不以「圖片」開頭、加標點；若圖片為純裝飾性（spacer/分隔線/背景），回傳 `is_decorative: true`；避免 keyword stuffing 和 HTML 特殊字符
- User prompt 包含：文章標題、分類名稱、圖片 URL（以 `image` content block 傳送）
- 模型：`claude-haiku-4-5-20251001`（短文本生成，成本最優）
- **圖片 URL 去重快取**（Deepening #1）：同一 URL 只呼叫 Vision 一次，快取結果持久化到 state 檔案；內嵌圖片階段複用快取避免重複呼叫
- 品質閘門：長度 30-150 字元、不含「image of / photo of / 圖片的」、不含未轉義的 HTML 特殊字符；同一篇文章內的多張圖片 alt text 不應完全相同

**Patterns to follow:**
- `scripts/yolo-lab-geo-optimizer-v1.js` — Claude tool_use 結構化輸出模式

**Test scenarios:**
- Happy path: 輸入音樂文章的圖片 URL → 產出包含音樂相關關鍵字的繁體中文 alt text，80-125 字元
- Happy path: 輸入電影文章的圖片 URL → 產出包含電影名稱/演員的 alt text
- Edge case: 圖片 URL 無法存取（404 / CDN 封鎖）→ 降級為純文字推測模式（僅用標題+分類）
- Edge case: 圖片為純文字截圖 → alt text 包含截圖中的文字內容
- Edge case: 生成結果超過 150 字元 → 自動重試一次，仍超過則截斷
- Edge case: Claude Vision 判斷圖片為裝飾性 → `is_decorative: true`，保持 `alt=""`
- Edge case: 同一圖片 URL 已在快取中 → 直接返回快取結果，不呼叫 API
- Error path: Claude API 回傳錯誤 → 記錄失敗、繼續處理下一張

**Verification:**
- 以 `--sample 5 --dry-run` 執行，檢查生成的 alt text 品質
- 所有生成結果通過長度和禁用詞品質閘門

---

- [ ] **Unit 3: Featured Media Alt Text 批次更新**

**Goal:** 批次更新 WordPress.com 媒體庫的 featured_media alt text

**Requirements:** R4, R7, R8

**Dependencies:** Unit 2

**Files:**
- Modify: `scripts/image-alt-text-optimizer.js`
- Output: `seo-optimization-output/alt-text-backup-featured.json`
- Output: `seo-optimization-output/state_alttext_featured.json`

**Approach:**
- 更新前備份：存 `{ mediaId, originalAlt }` 到 backup JSON
- 使用 `POST /rest/v1.1/sites/{siteId}/media/{mediaId}` 更新 `alt` 欄位
- **API 超時和重試**（Deepening #4, #5）：每個 API 調用設 30 秒超時，指數退避重試 3 次，速率限制檢測
- 認證：Bearer token（`WPCOM_TOKEN` env var → `.env` → `.mcp.json`）
- Rate limiting：batch size 5、delay 2000ms（Phase 9 驗證的保守策略），429 時自動增加延遲
- **執行後驗証**（Deepening #6）：每次更新後立即 `GET /media/{id}` 驗証，確認 `alt` 欄位已正確寫入，不匹配則記錄為 verification_failed
- State management：每批處理後存 checkpoint，記錄 `{ processed, failed, skipped, verification_failed }`，支援 `--resume`
- 失敗處理：指數退避重試 3 次，仍失敗則記錄到 `failed` 陣列；驗証失敗記錄到 `verification_failed`，兩者都繼續處理下一項
- CLI 參數：`--phase featured`、`--dry-run`、`--resume`、`--sample N`、`--skip-verification`（可選跳過驗証以加速）

**Patterns to follow:**
- `scripts/wp-seo-batch-v3.js` — Queue 類別、checkpoint、skip 邏輯
- `scripts/internal-linker-v2.js` — 429 偵測、指數退避

**Test scenarios:**
- Happy path: 更新 5 張 featured_media 的 alt text → API 回傳成功、state 正確記錄
- Happy path: `--dry-run` 模式 → 生成 alt text 但不發送更新請求
- Happy path: `--resume` → 從上次中斷處繼續，已處理項目不重複
- Edge case: 同一張圖片被多篇文章引用為 featured_media → 只更新一次（去重）
- Error path: API 429 → 等待 30 秒後重試
- Error path: 更新失敗 → 記錄到 failed 陣列、繼續下一張

**Verification:**
- 重新 GET 已更新的 media，確認 `alt` 欄位已寫入
- backup JSON 包含所有更新前的原始值
- state 檔案正確追蹤 processed/failed/skipped 數量

---

- [ ] **Unit 4: 內嵌圖片 Alt Text 批次更新**

**Goal:** 解析文章 HTML 中的 `<img>` 標籤，補充缺失的 alt 屬性並更新文章內容

**Requirements:** R5, R7, R8

**Dependencies:** Unit 2（建議在 Unit 3 完成後執行作為風險控制，但技術上可獨立運行）

**Files:**
- Modify: `scripts/image-alt-text-optimizer.js`
- Output: `seo-optimization-output/alt-text-backup-inline.json`
- Output: `seo-optimization-output/state_alttext_inline.json`

**Approach:**
- **冪等性設計**（Deepening #1）：為每張圖片的 URL 建立去重鍵 `{ imageUrl, generatedAlt }`，state 記錄已處理的 URL；即使同一篇文章有重複圖片，也只呼叫一次 Vision
- 使用 wp/v2 API 的 `context=edit` 取得文章 `content.raw`（包含 Gutenberg block comments），遵循 `internal-linker-v2.js` 的模式
- 以正則 `<img[^>]*>` 提取 `<img>` 標籤，僅修改 `alt` 屬性，保留其餘 HTML 結構和 block comments 不動
- 對缺少 alt 或 alt 為檔名的 `<img>` 生成 alt text（複用 Unit 2 引擎 + URL 去重快取）
- **部分失敗和細粒度恢復**（Deepening #1）
  - 一篇文章有 N 張圖片，逐張處理，記錄每張的狀態（成功/失敗/跳過）
  - 若第 M 張失敗，仍更新成功的圖片並 POST。State 記錄 `{ postId, status: 'partial', completedImages: [url1, url2], failedImages: [url3] }`
  - Resume 時僅重新處理 `failedImages`，已完成的圖片跳過
- 使用 wp/v2 API `POST /wp/v2/sites/{siteId}/posts/{postId}` 更新 `content.raw`，每次設 30 秒超時，失敗後指數退避重試
- **執行後驗証**（Deepening #6）：更新後立即 `GET /posts/{id}?context=edit`，驗証 `<img>` 標籤的 alt 屬性是否已正確寫入
- 備份：存原始 `content.raw` 到 backup JSON
- CLI 參數：`--phase inline`、`--skip-verification`（可選）
- 風險控制：每次只修改 `<img>` 的 alt 屬性，不改變其他 HTML 結構；啟動前檢查 `--phase scan` 的 audit report 是否存在

**Patterns to follow:**
- `scripts/yolo-lab-geo-optimizer-v1.js` — HTML block 注入模式（GEO summary/FAQ 注入）

**Test scenarios:**
- Happy path: 文章含 3 張內嵌圖片，2 張缺 alt → 僅修改缺 alt 的 2 張，第 3 張保持不變
- Edge case: `<img>` 在 Gutenberg block comment 內 `<!-- wp:image {"id":123} --><figure><img src="..." alt=""/></figure><!-- /wp:image -->` → 正確解析並更新
- Edge case: 文章無內嵌圖片 → 跳過，不發送更新請求
- Edge case: `<img>` 已有合理 alt text → 跳過
- Error path: HTML 解析產出異常結果（標籤不匹配）→ 跳過該文章、記錄錯誤
- Integration: 更新後重新取得文章 content，確認 `<img>` alt 已正確寫入且其他 HTML 未被修改

**Verification:**
- 抽檢 10 篇已更新文章的 HTML，確認僅 `<img>` alt 被修改、其他結構完整
- backup JSON 包含所有更新前的原始 content

---

- [ ] **Unit 5: 回滾機制**

**Goal:** 實作 `--rollback` 模式，從 backup JSON 讀取原始值並還原 WordPress 資料

**Requirements:** R8

**Dependencies:** Unit 3, Unit 4（需要 backup JSON 格式定義）

**Files:**
- Modify: `scripts/image-alt-text-optimizer.js`

**Approach:**
- **回滾順序明確化**（Deepening #7）：若同時啟動 `--rollback all`，執行順序為：
  1. 先回滾 inline images（按倒序：最後更新的文章先回滾），確保文章內容完整
  2. 再回滾 featured_media（按倒序）
  3. 驗証每次回滾後的結果
  - 此順序避免文章停留在中間狀態（featured_media 已回滾但內嵌圖片未回滾）
- `--rollback featured`：從 `alt-text-backup-featured.json` 讀取 `{ mediaId, originalAlt }`，呼叫 `POST /media/{id}` 還原 `alt` 欄位
- `--rollback inline`：從 `alt-text-backup-inline.json` 讀取 `{ postId, originalContent }`，呼叫 `POST /posts/{id}` 還原 `content`，驗証還原後的 HTML 是否完整
- 支援 `--rollback all`（兩者皆還原，按上述順序）和範圍指定（`--rollback featured --range 1-100`）
- API 超時和重試：與更新階段相同（30 秒超時、指數退避、batch 5、delay 2000ms）
- 驗証機制：回滾後立即驗証，確認值已還原到 backup 中記錄的原始值

**Patterns to follow:**
- `docs/PLAN_REMEDIATION_GUIDE_2026-04-08.md` — backup/restore 設計模式

**Test scenarios:**
- Happy path: 還原 5 張 featured_media 的 alt → 確認回到原始值
- Happy path: 還原 3 篇文章的 content → 確認 HTML 完整還原
- Edge case: backup 檔案不存在 → 顯示清楚錯誤訊息並退出
- Error path: 還原過程中 API 失敗 → 記錄失敗項目、繼續還原其餘

**Verification:**
- 還原後重新 GET 資料，確認值與 backup JSON 中的原始值一致

---

- [ ] **Unit 6: 品質驗證報告與執行摘要**

**Goal:** 產出執行報告，包含更新統計和失敗項目清單

**Requirements:** R6

**Dependencies:** Unit 3, Unit 4

**Files:**
- Modify: `scripts/image-alt-text-optimizer.js`
- Output: `seo-optimization-output/alt-text-optimization-report.md`

**Approach:**
- 彙整 featured_media 和 inline 兩階段的 state 檔案
- 統計：總圖片數、已更新數、跳過數（含裝飾性圖片）、失敗數、partial 文章數
- 品質分析：alt text 長度分布、裝飾性圖片比例
- 生成 Markdown 摘要報告，可直接貼入 vault journal
- CLI 參數：`--phase report`

**Patterns to follow:**
- `scripts/phase-21-27-batch-seo-optimizer.js` — 批次報告產出模式

**Test scenarios:**
- Happy path: 兩階段處理完成後，報告正確反映所有統計數字
- Edge case: 某階段全部失敗 → 報告標示警告並列出失敗原因分布

**Verification:**
- Markdown 報告可讀且包含可操作的後續建議

## Reliability Hardening & Testing Plan

基於深化審視的可靠性發現，實施前需驗証以下機制：

### 認證與鎖定機制
- [ ] **API 健檢**：Unit 1 啟動時驗証媒體讀寫、文章讀寫權限，失敗則退出
- [ ] **並發鎖**：檔案鎖測試——啟動兩個腳本進程，驗証是否只有一個獲得鎖
- [ ] **鎖超時**：若鎖持有者異常終止，後續進程是否能在 5 分鐘後自動取得鎖

### API 可靠性
- [ ] **超時保護**：模擬 45 秒無響應的 Claude API，驗証腳本是否在 45 秒後超時並降級
- [ ] **重試邏輯**：模擬間歇性 500 錯誤，驗証指數退避重試是否在 3 次後停止
- [ ] **速率限制檢測**：模擬 429 響應，驗証是否自動增加延遲並繼續重試

### 驗証機制
- [ ] **執行後驗証**：更新 5 張 featured_media，立即驗証是否已正確寫入（re-fetch 比對）
- [ ] **部分驗証失敗**：模擬 WordPress API 靜默失敗（返回 200 但未實際寫入），驗証是否被檢測
- [ ] **HTML 驗証**：更新 3 篇含內嵌圖片的文章，驗証 HTML 結構是否完整（block comments 未被破壞）

### 冪等性與恢復
- [ ] **URL 去重**：同一圖片出現在 5 篇文章中，驗証是否只呼叫 1 次 Claude Vision
- [ ] **部分失敗恢復**：中斷某篇文章的 5 張圖片處理（第 3 張時中斷），`--resume` 時驗証是否僅重新處理未完成的圖片
- [ ] **回滾順序**：更新後立即回滾，驗証順序是否為「inline → featured」，且文章狀態是否一致

### 邊界情況
- [ ] **無 featured_media 文章**：跳過時是否正確記錄
- [ ] **內嵌圖片無 alt 屬性** vs **alt="" vs alt="IMG_123"**：分類是否正確
- [ ] **Gutenberg block 內 img**：HTML 解析是否保留 block comments
- [ ] **特殊字符 alt text**：包含引號、HTML 標籤的生成結果是否被清理

## System-Wide Impact

- **Interaction graph:** 腳本讀寫 WordPress.com 的 `media` 和 `posts` endpoint；與現有 SEO batch 腳本共用認證 token 和 rate limit 空間（不應同時運行）
- **Error propagation:** Claude API 失敗 → 記錄並跳過單張圖片；WordPress API 失敗 → 指數退避重試 3 次後記錄失敗
- **State lifecycle risks:** 內嵌圖片更新涉及修改文章 content，若中斷可能導致部分更新。備份機制 + `--rollback` 確保可還原。`partial` 狀態追蹤文章內單張圖片的處理進度
- **API surface parity:** 本腳本使用 REST API v1.1（media）和 wp/v2（posts content），不影響 MCP 或其他 API 介面。不應與其他 batch 腳本同時運行以避免 rate limit 衝突
- **Unchanged invariants:** 現有 SEO meta（title、description）、Schema markup、internal links 不受影響；圖片 URL 和媒體檔案本身不變

## Risks & Dependencies

| Risk | Likelihood | Mitigation | Status |
|------|-----------|------------|--------|
| Claude Vision 無法存取部分 WordPress CDN 圖片 | Medium | 降級為純文字推測模式（標題+分類），並在報告中標記；cache 確保多篇文章共用圖片時只降級一次 | ✅ |
| 內嵌圖片 HTML 修改破壞文章格式 | Low | 預備份 content.raw；僅修改 `<img>` alt 屬性；執行後驗証 HTML 完整性；block comments 保留不動 | ✅ |
| API rate limit 導致大量 429 | Medium | 保守策略（batch 5、delay 2000ms）；指數退避；速率限制檢測自動增延遲；分多天執行 | ✅ |
| 生成的 alt text 關鍵字堆砌觸發 Google spam 偵測 | Low | Prompt 明確禁止 keyword stuffing；品質閘門過濾；HTML 特殊字符清理 | ✅ |
| WordPress.com 媒體 API `alt` 欄位行為與預期不同 | Low | Unit 1 先以 1-2 張圖片手動驗証 API 行為，驗証後回滾 | ✅ |
| **並發衝突導致 state 檔案損壞**（新增） | Medium → Low | 檔案互斥鎖；同時執行檢測 | ✅ Deepening #3 |
| **API 超時導致批次掛起**（新增） | High → Low | 30-60 秒超時 + 指數退避重試 + 失敗記錄 | ✅ Deepening #4 |
| **執行後無驗証導致靜默失敗**（新增） | High → Low | re-fetch 比對；verification_failed 狀態追蹤 | ✅ Deepening #6 |
| **部分失敗導致重複優化和成本增加**（新增） | Medium → Low | URL 冪等鍵；粒度化 state 記錄（completedImages）；resume 跳過已完成項 | ✅ Deepening #1 |

## Sources & References

- **Origin document:** [10x 流量成長策略](docs/brainstorms/2026-04-08-10x-traffic-growth-requirements.md)
- **Related plan:** [GEO 優化計畫](docs/plans/2026-04-10-001-feat-yololab-geo-optimization-plan.md)
- Related code: `scripts/wp-seo-batch-v3.js`, `scripts/internal-linker-v2.js`, `scripts/yolo-lab-geo-optimizer-v1.js`
- External: [Google Search Central — Image SEO](https://developers.google.com/search/docs/appearance/google-images), [WCAG 2.1 §1.1.1](https://www.w3.org/TR/WCAG21/#non-text-content)
