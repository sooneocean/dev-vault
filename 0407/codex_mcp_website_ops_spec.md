#Codex交付版｜PHP網站文章系統＋標籤總庫＋分類頁SEO的完整MCP實作規格

##1.專案目標

在既有PHP網站中新增一套可由MCP客戶端呼叫的網站營運能力層，讓AI可以安全地參與以下工作流：

1.文章草稿建立
2.文章發布
3.文章SEO補洞
4.分類頁SEO補洞
5.標籤總庫查詢與指派
6.站點資產重建與快取清除

本規格的交付物不是獨立CMS，而是「既有PHP網站旁邊新增一個MCP服務層」，共用同一份資料庫與商業邏輯。

---

##2.範圍

###2.1本次要做
-文章系統的MCP能力
-標籤總庫的MCP能力
-分類頁SEO的MCP能力
-遠端HTTP型MCP Server
-本機STDIO型MCP Server
-基本Bearer Token保護
-Nginx反向代理
-Supervisor常駐啟動
-可供AI讀取的Resources
-可供AI執行的Tools
-可供AI套用的Prompts

###2.2本次不要做
-刪除文章
-刪除分類
-刪除標籤
-會員系統整合
-OAuth2.1正式授權流程
-前台UI改版
-後台管理介面改版
-非必要的批次長任務系統
-Queue與Job Worker
-多租戶權限系統

---

##3.設計原則

###3.1架構原則
-不要把MCP能力直接塞進既有controller
-所有資料操作先收斂到Service層
-MCP只呼叫Service，不直接散落SQL
-所有寫入操作都應有對應的讀取Resource
-所有危險操作預設不開放
-發布後一定執行收尾動作

###3.2安全原則
-僅提供新增、查詢、更新、發布，不提供刪除
-HTTP模式必須驗證Authorization Bearer Token
-遠端MCP服務只綁127.0.0.1，對外由Nginx反代
-所有Tool都應可被審計與記錄
-所有寫入前建議先讀取snapshot Resource

###3.3命名原則
-Tool名稱使用snake_case
-Resource URI使用ops://前綴
-Prompt名稱使用snake_case
-資料表欄位盡量語意化，不使用模糊縮寫

---

##4.高階架構

```text
AI Client(ChatGPT/Cursor/Claude)
        │
        ▼
Remote MCP Client Config
        │
        ▼
Nginx(https://mcp.example.com/mcp)
        │
        ▼
PHP MCP Server(Streamable HTTP)
        │
        ├─WebsiteOpsTools
        ├─WebsiteOpsResources
        └─WebsiteOpsPrompts
        │
        ▼
Service Layer
        ├─ArticleService
        ├─CategoryService
        ├─TagLibraryService
        ├─SeoAuditService
        └─InfraService
        │
        ▼
MySQL
```

本機開發時可改為：

```text
AI Client
   │
   ▼
stdio-server.php
   │
   ▼
同一套Service Layer與資料庫
```

---

##5.技術假設

-語言：PHP8.1+
-套件管理：Composer
-MCP SDK：php-mcp/server
-資料庫：MySQL8或相容版本
-HTTP入口：Nginx反向代理
-常駐行程：Supervisor
-程式風格：PSR-4
-資料存取：PDO
-部署型態：CLI常駐MCP服務＋既有網站服務

---

##6.資料表設計

###6.1articles

```sql
CREATE TABLE articles (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  content LONGTEXT NOT NULL,
  excerpt TEXT NULL,
  status ENUM('draft','review','scheduled','published','archived') NOT NULL DEFAULT 'draft',
  featured_image_url VARCHAR(512) NULL,
  canonical_url VARCHAR(512) NULL,
  meta_title VARCHAR(255) NULL,
  meta_description VARCHAR(320) NULL,
  og_title VARCHAR(255) NULL,
  og_description VARCHAR(320) NULL,
  og_image_url VARCHAR(512) NULL,
  category_id BIGINT UNSIGNED NULL,
  published_at DATETIME NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  INDEX idx_articles_status(status),
  INDEX idx_articles_category(category_id),
  INDEX idx_articles_published_at(published_at)
);
```

###6.2categories

```sql
CREATE TABLE categories (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  parent_id BIGINT UNSIGNED NULL,
  name VARCHAR(120) NOT NULL,
  slug VARCHAR(120) NOT NULL UNIQUE,
  description TEXT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  INDEX idx_categories_parent(parent_id)
);
```

###6.3category_seo

```sql
CREATE TABLE category_seo (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  category_id BIGINT UNSIGNED NOT NULL UNIQUE,
  meta_title VARCHAR(255) NULL,
  meta_description VARCHAR(320) NULL,
  canonical_url VARCHAR(512) NULL,
  og_title VARCHAR(255) NULL,
  og_description VARCHAR(320) NULL,
  og_image_url VARCHAR(512) NULL,
  h1_title VARCHAR(255) NULL,
  intro_copy TEXT NULL,
  robots_directive VARCHAR(120) NULL,
  updated_at DATETIME NOT NULL
);
```

###6.4tag_libraries

```sql
CREATE TABLE tag_libraries (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  description TEXT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);
```

###6.5tags

```sql
CREATE TABLE tags (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  library_id BIGINT UNSIGNED NOT NULL,
  parent_id BIGINT UNSIGNED NULL,
  name VARCHAR(120) NOT NULL,
  slug VARCHAR(120) NOT NULL UNIQUE,
  description TEXT NULL,
  tag_type ENUM('topic','entity','format','intent','audience','campaign','other') NOT NULL DEFAULT 'topic',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  INDEX idx_tags_library(library_id),
  INDEX idx_tags_parent(parent_id)
);
```

###6.6tag_aliases

```sql
CREATE TABLE tag_aliases (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  tag_id BIGINT UNSIGNED NOT NULL,
  alias_name VARCHAR(120) NOT NULL,
  alias_slug VARCHAR(120) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL
);
```

###6.7article_tags

```sql
CREATE TABLE article_tags (
  article_id BIGINT UNSIGNED NOT NULL,
  tag_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY(article_id, tag_id)
);
```

###6.8category_seo_templates

```sql
CREATE TABLE category_seo_templates (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  category_id BIGINT UNSIGNED NOT NULL UNIQUE,
  title_template VARCHAR(255) NULL,
  description_template VARCHAR(320) NULL,
  canonical_template VARCHAR(512) NULL,
  updated_at DATETIME NOT NULL
);
```

###6.9建議外鍵
實作時依既有系統風險評估是否補上外鍵；若既有資料品質不一，第一版可先不上外鍵、先完成功能，再進行資料清理與約束升級。

---

##7.目錄結構

```text
project-root/
├─composer.json
├─.env.example
├─src/
│ ├─Services/
│ │ ├─ArticleService.php
│ │ ├─CategoryService.php
│ │ ├─TagLibraryService.php
│ │ ├─SeoAuditService.php
│ │ └─InfraService.php
│ └─Mcp/
│   ├─WebsiteOpsTools.php
│   ├─WebsiteOpsResources.php
│   └─WebsiteOpsPrompts.php
├─mcp/
│ ├─stdio-server.php
│ └─http-server.php
├─config/
│ └─mcp.php
└─database/
  └─migrations/
```

---

##8.要暴露給MCP的能力清單

###8.1Tools
-`create_article_draft`
-`publish_article`
-`find_articles_missing_seo`
-`find_categories_missing_seo`
-`upsert_category_seo`
-`search_master_tags`
-`assign_article_tags`
-`rebuild_sitemap`
-`purge_category_cache`
-`purge_article_cache`

###8.2Resources
-`ops://dashboard/content-health`
-`ops://taxonomy/libraries`
-`ops://taxonomy/library/{libraryCode}`
-`ops://article/{articleId}/snapshot`
-`ops://category/{slug}/snapshot`

###8.3Prompts
-`generate_article_meta`
-`generate_category_seo`
-`classify_article_with_master_tags`

---

##9.核心PHP檔案要求

###9.1ArticleService.php
必須提供：
-`createDraft()`
-`publishArticle()`
-`getArticleSnapshot()`
-`listRecentArticles()`

要求：
-使用PDO prepared statements
-發布時只更新狀態與published_at
-單篇snapshot需附帶分類與標籤資料

###9.2CategoryService.php
必須提供：
-`getCategorySnapshotBySlug()`
-`upsertCategorySeo()`
-`findCategoriesMissingSeo()`

要求：
-支援category_seo不存在時自動建立
-分類snapshot要同時回傳category主表與SEO覆寫資料

###9.3TagLibraryService.php
必須提供：
-`listLibraries()`
-`listTagsByLibraryCode()`
-`searchTags()`
-`assignArticleTags()`

要求：
-`searchTags()`需同時搜尋tags與tag_aliases
-`assignArticleTags()`需在transaction內先刪後插
-文章實際只掛主標籤，不直接掛alias

###9.4SeoAuditService.php
必須提供：
-`findArticlesMissingSeo()`
-`contentHealthSummary()`

要求：
-summary至少包含：
-缺文章SEO數
-缺分類SEO數
-草稿類文章數

###9.5InfraService.php
必須提供：
-`rebuildSitemap()`
-`purgeCategoryCache()`
-`purgeArticleCache()`

第一版可以先回傳stub response，但介面要先固定，方便後續接真實快取系統與站點生成器。

---

##10.MCP實作要求

###10.1WebsiteOpsTools.php
使用PHP8 Attributes實作Tool定義。
所有Tool輸出統一為array，至少包含：
-`ok`
-`message`
-核心ID或items

Tool不得直接寫SQL，必須呼叫Service。

###10.2WebsiteOpsResources.php
所有Resource mimeType使用`application/json`。
Resource應優先提供AI決策前所需脈絡，不做寫入。

###10.3WebsiteOpsPrompts.php
Prompt只負責輸出固定工作流模板，不負責資料寫入。
Prompt名稱穩定，不應在小改版中頻繁變動。

---

##11.伺服器啟動檔要求

###11.1mcp/stdio-server.php
用途：
-本機開發
-本機MCP client測試
-快速驗證Tool與Resource是否可被列出與呼叫

要求：
-使用`StdioServerTransport`
-所有非MCP輸出只能寫到STDERR
-透過`BasicContainer`注入PDO與Services
-透過`discover()`掃描`src/Mcp`

###11.2mcp/http-server.php
用途：
-正式環境
-遠端MCP client連線
-支援多客戶端

要求：
-使用`StreamableHttpServerTransport`
-host綁`127.0.0.1`
-port預設`8080`
-`mcpPathPrefix`設為`mcp`
-第一版使用`enableJsonResponse: true`
-第一版使用`stateless: true`
-中介層驗證`Authorization: Bearer <token>`
-啟動時注入所有Services與PDO
-掃描`src/Mcp`

---

##12..env.example

```env
APP_ENV=local

DB_DSN=mysql:host=127.0.0.1;dbname=yourdb;charset=utf8mb4
DB_USER=root
DB_PASS=secret

MCP_API_KEY=replace-with-strong-secret
MCP_HOST=127.0.0.1
MCP_PORT=8080
MCP_PATH_PREFIX=mcp
```

---

##13.composer.json要求

```json
{
  "name": "your-company/website-ops-mcp",
  "type": "project",
  "require": {
    "php": "^8.1",
    "php-mcp/server": "^4.0"
  },
  "autoload": {
    "psr-4": {
      "App\\\": "src/"
    }
  }
}
```

如果既有專案已經有composer.json，請僅合併必要設定，不要覆蓋既有autoload與require。

---

##14.Nginx設定

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.example.com;

    location /mcp {
        proxy_pass http://127.0.0.1:8080/mcp;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Authorization $http_authorization;

        proxy_buffering off;
    }
}
```

備註：
-不要讓外部直接連8080
-正式網域請使用HTTPS
-若後續切換為SSE模式，`proxy_buffering off`保留

---

##15.Supervisor設定

```ini
[program:website-ops-mcp]
command=/usr/bin/php /var/www/project-root/mcp/http-server.php
directory=/var/www/project-root
autostart=true
autorestart=true
stderr_logfile=/var/log/website-ops-mcp.err.log
stdout_logfile=/var/log/website-ops-mcp.out.log
environment=DB_DSN="mysql:host=127.0.0.1;dbname=yourdb;charset=utf8mb4",DB_USER="root",DB_PASS="secret",MCP_API_KEY="replace-with-strong-secret"
```

---

##16.交付順序

###階段A：基礎建設
1.安裝`php-mcp/server`
2.建立PSR-4目錄
3.建立PDO注入
4.建立stdio-server.php
5.建立http-server.php
6.確認MCP client能列出Tools/Resources/Prompts

###階段B：資料表
1.新增articles相關欄位
2.建立categories
3.建立category_seo
4.建立tag_libraries
5.建立tags
6.建立tag_aliases
7.建立article_tags
8.建立category_seo_templates

###階段C：Service層
1.完成ArticleService
2.完成CategoryService
3.完成TagLibraryService
4.完成SeoAuditService
5.完成InfraService

###階段D：MCP元素
1.完成WebsiteOpsTools
2.完成WebsiteOpsResources
3.完成WebsiteOpsPrompts

###階段E：部署
1.Nginx反向代理
2.Supervisor啟動
3.遠端client config
4.API key驗證

###階段F：驗收
1.資源可讀
2.工具可調
3.分類頁SEO可寫
4.標籤總庫可查
5.文章可建立草稿
6.文章可發布
7.發布後可執行收尾動作

---

##17.驗收案例

###17.1Resource驗收
-能讀`ops://dashboard/content-health`
-能讀`ops://taxonomy/libraries`
-能讀`ops://taxonomy/library/general`
-能讀`ops://article/1/snapshot`
-能讀`ops://category/ai-tools/snapshot`

###17.2Tool驗收
-呼叫`create_article_draft`可建立草稿
-呼叫`publish_article`可改為published
-呼叫`find_articles_missing_seo`可列出缺漏內容
-呼叫`find_categories_missing_seo`可列出缺漏分類
-呼叫`search_master_tags`可搜到主標籤與alias命中結果
-呼叫`assign_article_tags`可成功更新article_tags
-呼叫`upsert_category_seo`可寫入category_seo
-呼叫`rebuild_sitemap`回傳成功訊息
-呼叫`purge_category_cache`回傳成功訊息
-呼叫`purge_article_cache`回傳成功訊息

###17.3Prompt驗收
-可列出三個Prompt
-可依articleId產出文章meta文案
-可依categorySlug產出分類頁SEO文案
-可依preferredLibrary產出標籤建議

---

##18.給Codex的限制條件

1.不得刪除既有網站功能
2.不得直接修改既有前台路由行為
3.不得在controller內散落SQL
4.不得把MCP能力做成只能本機用的玩具版本
5.不得新增刪除型Tool
6.不得把access token放進query string
7.不得在STDIO模式把debug輸出到STDOUT
8.不得把標籤alias直接掛到article_tags
9.不得讓MCP服務直接對外暴露8080
10.所有寫入型Tool都要回傳結構化結果

---

##19.給Codex的實作提示

請依以下順序產出程式碼與檔案：

1.先建立migration SQL或migration檔
2.再建立Services
3.再建立Mcp目錄下三個檔案
4.再建立stdio-server.php與http-server.php
5.再補`.env.example`
6.再補Nginx與Supervisor範例
7.最後補README，說明本機與遠端如何測試

寫程式時請遵守：
-嚴格型別
-避免魔術字串分散
-盡量使用小而穩定的方法
-輸入用prepared statements
-輸出統一結構
-必要處加上RuntimeException
-先可用，再優化

---

##20.給Codex的最終開工Prompt

```text
請在既有PHP專案中實作一套完整的MCP服務層，使用php-mcp/server，目標是支援文章系統、標籤總庫與分類頁SEO的網站營運流程。

請依照以下要求開發：

1.使用PHP8.1+與Composer
2.建立以下目錄：
- src/Services/
- src/Mcp/
- mcp/
- config/
- database/migrations/

3.建立以下Service：
- ArticleService
- CategoryService
- TagLibraryService
- SeoAuditService
- InfraService

4.建立以下MCP元素：
- WebsiteOpsTools
- WebsiteOpsResources
- WebsiteOpsPrompts

5.建立以下MCP入口：
- mcp/stdio-server.php
- mcp/http-server.php

6.資料表需求：
- articles
- categories
- category_seo
- tag_libraries
- tags
- tag_aliases
- article_tags
- category_seo_templates

7.必須實作以下Tools：
- create_article_draft
- publish_article
- find_articles_missing_seo
- find_categories_missing_seo
- upsert_category_seo
- search_master_tags
- assign_article_tags
- rebuild_sitemap
- purge_category_cache
- purge_article_cache

8.必須實作以下Resources：
- ops://dashboard/content-health
- ops://taxonomy/libraries
- ops://taxonomy/library/{libraryCode}
- ops://article/{articleId}/snapshot
- ops://category/{slug}/snapshot

9.必須實作以下Prompts：
- generate_article_meta
- generate_category_seo
- classify_article_with_master_tags

10.限制：
-不要實作刪除型Tool
-不要改壞既有網站流程
-不要把MCP能力塞進既有controller
-所有資料操作集中在Service層
-STDIO模式不得輸出非MCP內容到STDOUT
-HTTP模式使用Bearer Token中介層
-遠端MCP服務僅綁127.0.0.1，對外由Nginx代理

11.請同時產出：
- migration檔或SQL
- PHP程式碼
- .env.example
- Nginx範例
- Supervisor範例
- README測試說明

12.請先以可執行為優先，不要過度抽象。
```

---

##21.建議的本機測試語句

```text
請讀取ops://dashboard/content-health
請列出缺少SEO的分類頁
請讀取ops://taxonomy/library/general
請根據ops://article/15/snapshot，從general標籤庫選出最合適的標籤
請把文章15更新標籤為[3,8,19]
請為分類slug為ai-tools的頁面生成SEO文案
請將ai-tools分類頁SEO寫回資料庫
請建立一篇標題為AI與SEO自動化的草稿
請發布文章ID 15
```

---

##22.第二版可擴充方向

-改成OAuth2.1授權流程
-加入權限分級與scope
-加入批次SEO任務
-加入真正的cache adapter
-加入真正的sitemap generator
-加入文章內鏈建議
-加入排程發布
-加入站內搜尋索引重建
-加入分類頁模板規則引擎
-加入標籤治理報表

---

##23.完成定義

以下全部成立才算完成：

1.本機STDIO client能連上並列出Tools/Resources/Prompts
2.遠端HTTP client能透過Bearer Token連上
3.文章草稿可建立
4.文章可發布
5.文章snapshot可讀
6.分類snapshot可讀
7.標籤總庫可查
8.文章標籤可更新
9.分類頁SEO可寫入
10.content-health Resource可回傳正確摘要
11.Nginx與Supervisor配置可啟動正式服務
12.README中有本機與遠端測試方式
