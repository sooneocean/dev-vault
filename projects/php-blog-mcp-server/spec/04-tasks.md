# 04 — Implementation Tasks (SDD Task Breakdown)

## 開發階段

本文件將 SPEC 需求拆解為可執行的開發任務。每個任務需滿足其 Acceptance Criteria 後才算完成。

---

## Phase 1: 基礎建設 (Foundation)

### Task 1.1: 專案初始化
**Acceptance Criteria:**
- [ ] `pnpm init` 建立 package.json
- [ ] TypeScript strict mode 設定完成
- [ ] ESLint + Prettier 設定
- [ ] Vitest 測試框架設定
- [ ] `.gitignore` 排除 `.env`, `node_modules`, `dist`
- [ ] `.env.example` 範本建立
- [ ] 目錄結構建立（src/, tests/, spec/）

### Task 1.2: MCP Server 骨架
**Acceptance Criteria:**
- [ ] `@modelcontextprotocol/sdk` 安裝並能啟動
- [ ] `src/index.ts` 建立 McpServer 實例
- [ ] StdioServerTransport 連線成功
- [ ] 可透過 MCP client 驗證 server 回應 `initialize`

### Task 1.3: Logger 與 Error 處理
**Acceptance Criteria:**
- [ ] `src/utils/logger.ts` 結構化 JSON logging
- [ ] `src/utils/errors.ts` 自訂錯誤類型 (ApiError, AuthError, ValidationError)
- [ ] 錯誤轉換為 MCP 錯誤回應格式
- [ ] 單元測試覆蓋錯誤路徑

### Task 1.4: WordPress API Client
**Acceptance Criteria:**
- [ ] `src/client/wp-api-client.ts` 完成
- [ ] 支援 Application Password 認證 (Basic Auth)
- [ ] 自動 retry (可設定次數)
- [ ] 請求/回應攔截器記錄日誌
- [ ] 型別定義：Post, Category, Tag, Media, SiteSettings
- [ ] 單元測試（mock HTTP）

---

## Phase 2: 內容管理 Tools

### Task 2.1: 文章 CRUD Tools
**對應需求:** FR-1.1 ~ FR-1.5
**Acceptance Criteria:**
- [ ] `content_list_posts` — 支援 page, per_page, status, search, categories, tags 參數
- [ ] `content_get_post` — 依 ID 取得文章，含 meta data
- [ ] `content_create_post` — 支援 title, content, status, categories, tags
- [ ] `content_update_post` — 支援部分更新
- [ ] `content_delete_post` — 支援 force (永久刪除) 參數
- [ ] 每個 Tool 的 schema 使用 Zod 定義
- [ ] 整合測試（對 mock WP API）

### Task 2.2: 批次操作與排程
**對應需求:** FR-1.6, FR-1.7
**Acceptance Criteria:**
- [ ] `content_batch_update` — 接受 post IDs 陣列 + 更新資料
- [ ] 排程發佈：設定 `date` 為未來時間即自動排程
- [ ] 批次操作回傳成功/失敗結果摘要

---

## Phase 3: SEO 工具集 (核心價值)

### Task 3.1: SEO 分析引擎
**對應需求:** FR-2.2, FR-2.3
**Acceptance Criteria:**
- [ ] `src/seo-engine/analyzer.ts` 內容分析
- [ ] `src/seo-engine/scorer.ts` 五維度評分 (Title/Meta/結構/關鍵字/可讀性)
- [ ] `seo_analyze_content` Tool — 回傳分數 + 具體改善建議
- [ ] 支援中英文內容分析
- [ ] 單元測試覆蓋各評分維度

### Task 3.2: Meta Tags 自動生成
**對應需求:** FR-2.1, FR-2.5
**Acceptance Criteria:**
- [ ] `src/seo-engine/meta-generator.ts` 完成
- [ ] `seo_generate_meta` Tool — 輸入文章內容，輸出 title/description/og:*
- [ ] 生成品質：title 30-60 chars, description 120-160 chars
- [ ] 支援覆寫：可傳入自訂值覆蓋自動生成

### Task 3.3: Sitemap 與結構化資料
**對應需求:** FR-2.4, FR-2.7
**Acceptance Criteria:**
- [ ] `seo_generate_sitemap` — 產生 XML sitemap
- [ ] 支援 ping Google Search Console
- [ ] `seo_generate_schema` — 產生 Article JSON-LD
- [ ] Schema 驗證通過 Google Rich Results Test

### Task 3.4: 進階 SEO
**對應需求:** FR-2.6, FR-2.8, FR-2.9
**Acceptance Criteria:**
- [ ] `seo_suggest_internal_links` — 基於現有文章推薦連結
- [ ] 重導向管理 CRUD
- [ ] `seo_health_check` — 全站 SEO 健康掃描

---

## Phase 4: 分類、標籤、媒體

### Task 4.1: 分類與標籤管理
**對應需求:** FR-4.1 ~ FR-4.3
**Acceptance Criteria:**
- [ ] `taxonomies_list_categories` — 含父子關係
- [ ] `taxonomies_manage_categories` — CRUD
- [ ] `taxonomies_list_tags` / `taxonomies_manage_tags` — CRUD

### Task 4.2: 媒體管理
**對應需求:** FR-1.8
**Acceptance Criteria:**
- [ ] `media_list` — 列出媒體庫
- [ ] `media_upload` — 上傳檔案
- [ ] 支援圖片 metadata 回傳

---

## Phase 5: 分析與監控

### Task 5.1: 文章統計
**對應需求:** FR-3.1, FR-3.2
**Acceptance Criteria:**
- [ ] `analytics_post_stats` — 單篇文章瀏覽統計
- [ ] `analytics_top_posts` — 熱門文章排行（日/週/月）
- [ ] 介接方式：優先本地統計，後續接 GA API

### Task 5.2: 網站健康
**對應需求:** FR-3.3, FR-3.4, FR-5.1, FR-5.2
**Acceptance Criteria:**
- [ ] `site_get_settings` — 讀取網站設定
- [ ] `site_health_check` — 效能與連結檢查

---

## Phase 6: 整合與發布

### Task 6.1: 端到端整合測試
**Acceptance Criteria:**
- [ ] 使用 WordPress local dev (wp-env) 或 mock server 測試
- [ ] 所有 Tool 可透過 MCP client 正確呼叫
- [ ] 錯誤場景覆蓋（網路錯誤、認證失敗、無效參數）

### Task 6.2: 文件與發布
**Acceptance Criteria:**
- [ ] README.md 使用指南
- [ ] 每個 Tool 的 inline description 完整
- [ ] npm publish 或 GitHub release

---

## 任務依賴圖

```
Phase 1 (Foundation)
  1.1 ──▶ 1.2 ──▶ 1.3
              │
              └──▶ 1.4
                    │
Phase 2 ◀──────────┘
  2.1 ──▶ 2.2
                    │
Phase 3 ◀──────────┘
  3.1 ──▶ 3.2 ──▶ 3.3 ──▶ 3.4

Phase 4 (可與 Phase 3 並行)
  4.1 ──▶ 4.2

Phase 5 (需 Phase 2 + Phase 4)
  5.1 ──▶ 5.2

Phase 6 (需所有 Phase)
  6.1 ──▶ 6.2
```

## 建議開發順序

1. **先做 Phase 1** — 確保骨架能跑
2. **再做 Task 2.1 (CRUD)** — 最小可用功能
3. **接 Task 3.1 + 3.2** — 核心 SEO 價值
4. **其餘按需推進**
