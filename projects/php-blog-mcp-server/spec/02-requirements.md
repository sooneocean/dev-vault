# 02 — Requirements Specification

## 功能需求 (Functional Requirements)

### FR-1: 內容管理 (Content Management)

| ID | 需求 | 優先級 | Acceptance Criteria |
|----|------|--------|---------------------|
| FR-1.1 | 列出所有文章（支援分頁、篩選） | P0 | 可依 status/date/category 篩選，回傳 JSON |
| FR-1.2 | 取得單篇文章詳細內容 | P0 | 回傳 title, content, meta, SEO data |
| FR-1.3 | 建立新文章 | P0 | 支援 title, content, status, categories, tags |
| FR-1.4 | 更新文章 | P0 | 支援部分更新 (PATCH) |
| FR-1.5 | 刪除文章（含回收站） | P1 | 支援 soft delete / permanent delete |
| FR-1.6 | 批次操作文章 | P1 | 批次更新 status, categories, tags |
| FR-1.7 | 文章排程發佈 | P1 | 設定 future date 自動排程 |
| FR-1.8 | 媒體庫管理（上傳/列出/刪除） | P2 | 支援圖片與附件 |

### FR-2: SEO 優化

| ID | 需求 | 優先級 | Acceptance Criteria |
|----|------|--------|---------------------|
| FR-2.1 | 自動生成 meta title / description | P0 | 基於內容自動生成，可手動覆寫 |
| FR-2.2 | 關鍵字密度分析 | P0 | 回傳目標關鍵字的密度百分比 |
| FR-2.3 | SEO 評分與建議 | P0 | 0-100 分 + 具體改善建議列表 |
| FR-2.4 | Sitemap 生成與提交 | P0 | 生成 XML sitemap，支援 ping Google |
| FR-2.5 | Open Graph / Twitter Card 管理 | P1 | 自動生成 og:title, og:description, og:image |
| FR-2.6 | 內部連結建議 | P1 | 基於現有文章推薦相關內部連結 |
| FR-2.7 | Schema.org 結構化資料 | P1 | 自動生成 Article schema JSON-LD |
| FR-2.8 | 重導向管理 (301/302) | P2 | 建立/列出/刪除重導向規則 |
| FR-2.9 | 站點健康檢查 | P2 | 檢查 broken links, missing meta, slow pages |

### FR-3: 分析與監控

| ID | 需求 | 優先級 | Acceptance Criteria |
|----|------|--------|---------------------|
| FR-3.1 | 文章瀏覽量統計 | P1 | 連接 Google Analytics API 或本地統計 |
| FR-3.2 | 熱門文章排行 | P1 | 依時段篩選（日/週/月） |
| FR-3.3 | 關鍵字排名追蹤 | P2 | 追蹤目標關鍵字的搜尋排名變化 |
| FR-3.4 | 網站效能指標 | P2 | 頁面載入時間、Core Web Vitals |

### FR-4: 分類與標籤管理

| ID | 需求 | 優先級 | Acceptance Criteria |
|----|------|--------|---------------------|
| FR-4.1 | 列出/建立/更新/刪除分類 | P0 | 完整 CRUD |
| FR-4.2 | 列出/建立/更新/刪除標籤 | P0 | 完整 CRUD |
| FR-4.3 | 分類階層管理 | P1 | 支援父子關係 |

### FR-5: 網站設定

| ID | 需求 | 優先級 | Acceptance Criteria |
|----|------|--------|---------------------|
| FR-5.1 | 讀取網站基本設定 | P1 | site title, tagline, permalink structure |
| FR-5.2 | 更新網站設定 | P2 | 透過 MCP 更新網站選項 |

---

## 非功能需求 (Non-Functional Requirements)

| ID | 需求 | 指標 |
|----|------|------|
| NFR-1 | 回應時間 | P95 < 2s, P99 < 5s |
| NFR-2 | 併發處理 | 支援至少 10 個同時 MCP 連線 |
| NFR-3 | 安全性 | API Key 驗證、HTTPS only、無明文密碼儲存 |
| NFR-4 | 可觀測性 | 結構化 logging (JSON)，支援錯誤追蹤 |
| NFR-5 | 可擴展性 | 插件化架構，新工具可熱加載 |
| NFR-6 | 相容性 | Node.js ≥ 18, MCP SDK ≥ 1.x |
| NFR-7 | 文件完整性 | 每個 Tool 需有 description + schema 定義 |

---

## MCP Tools 定義總覽

以下是預計提供的 MCP Tools，按功能域分組：

```
content/
  list_posts          - 列出文章
  get_post            - 取得文章
  create_post         - 建立文章
  update_post         - 更新文章
  delete_post         - 刪除文章
  batch_update_posts  - 批次更新文章

seo/
  analyze_content     - 分析內容 SEO 評分
  generate_meta       - 生成 meta tags
  generate_sitemap    - 生成 sitemap
  check_keywords      - 關鍵字分析
  suggest_internal_links - 內部連結建議
  generate_schema     - 生成結構化資料

taxonomies/
  list_categories     - 列出分類
  manage_categories   - 管理分類
  list_tags           - 列出標籤
  manage_tags         - 管理標籤

media/
  list_media          - 列出媒體
  upload_media        - 上傳媒體

analytics/
  get_post_stats      - 文章統計
  get_top_posts       - 熱門文章

site/
  get_settings        - 網站設定
  health_check        - 健康檢查
```
