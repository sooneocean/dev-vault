# 03 — Technical Design

## 系統架構

```
┌─────────────────────────────────────────────────────┐
│                  AI Agent (Claude)                   │
│                  + MCP Client                       │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (stdio/HTTP)
┌──────────────────────▼──────────────────────────────┐
│           php-blog-mcp-server (Node.js)              │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ MCP Layer │  │ Tool     │  │ SEO Engine       │   │
│  │ (SDK)    │──│ Router   │──│ (Analysis/Score) │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                        │                             │
│  ┌─────────────────────▼─────────────────────────┐   │
│  │           WordPress REST API Client            │   │
│  │        (wp-api-client.ts)                      │   │
│  └─────────────────────┬─────────────────────────┘   │
└────────────────────────┼────────────────────────────┘
                         │ HTTPS (REST API)
┌────────────────────────▼────────────────────────────┐
│              WordPress PHP Site                      │
│         (wp-json/wp/v2/...)                          │
└─────────────────────────────────────────────────────┘
```

## 技術選型

| 元件 | 技術 | 理由 |
|------|------|------|
| Runtime | Node.js ≥ 18 | MCP SDK 原生支援 |
| Language | TypeScript (strict) | 型別安全，減少執行期錯誤 |
| MCP SDK | `@modelcontextprotocol/sdk` | 官方 SDK |
| HTTP Client | `axios` + interceptors | 成熟穩定，支援 retry |
| Testing | Vitest | 快速，原生 TS 支援 |
| Linting | ESLint + Prettier | 程式碼品質一致 |
| Package Manager | pnpm | 快速、省空間 |

## 目錄結構

```
php-blog-mcp-server/
├── spec/                          # SDD 規格文件
│   ├── 01-vision.md              # 產品願景
│   ├── 02-requirements.md        # 需求規格
│   ├── 03-design.md              # 技術設計 (本文件)
│   └── 04-tasks.md               # 實作任務分解
├── src/
│   ├── index.ts                   # MCP Server 入口
│   ├── config.ts                  # 環境設定
│   ├── client/
│   │   └── wp-api-client.ts      # WordPress REST API 封裝
│   ├── tools/
│   │   ├── index.ts              # Tool 註冊中心
│   │   ├── content.ts            # 內容管理 Tools
│   │   ├── seo.ts                # SEO Tools
│   │   ├── taxonomies.ts         # 分類/標籤 Tools
│   │   ├── media.ts              # 媒體管理 Tools
│   │   ├── analytics.ts          # 分析 Tools
│   │   └── site.ts               # 網站設定 Tools
│   ├── seo-engine/
│   │   ├── analyzer.ts           # 內容分析引擎
│   │   ├── scorer.ts             # SEO 評分計算
│   │   ├── meta-generator.ts     # Meta tags 生成
│   │   └── schema-generator.ts   # Schema.org 生成
│   └── utils/
│       ├── logger.ts             # 結構化日誌
│       └── errors.ts             # 自訂錯誤類型
├── tests/
│   ├── unit/
│   └── integration/
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

## 核心模組設計

### 1. MCP Server 入口 (`src/index.ts`)

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAllTools } from "./tools/index.js";

const server = new McpServer({
  name: "php-blog-mcp-server",
  version: "1.0.0",
});

registerAllTools(server);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 2. WordPress API Client (`src/client/wp-api-client.ts`)

```typescript
export class WpApiClient {
  constructor(config: { baseUrl: string; username: string; appPassword: string });

  // Posts
  async listPosts(params?: ListParams): Promise<PaginatedResult<Post>>;
  async getPost(id: number): Promise<Post>;
  async createPost(data: CreatePostInput): Promise<Post>;
  async updatePost(id: number, data: UpdatePostInput): Promise<Post>;
  async deletePost(id: number, force?: boolean): Promise<void>;

  // Taxonomies
  async listCategories(params?: ListParams): Promise<Category[]>;
  async listTags(params?: ListParams): Promise<Tag[]>;

  // Media
  async listMedia(params?: ListParams): Promise<Media[]>;
  async uploadMedia(file: Buffer, filename: string): Promise<Media>;

  // Settings
  async getSettings(): Promise<SiteSettings>;
}
```

### 3. SEO 分析引擎 (`src/seo-engine/analyzer.ts`)

評分維度 (各 20 分，滿分 100)：

| 維度 | 檢查項目 |
|------|----------|
| Title | 長度 (30-60 chars)、包含關鍵字 |
| Meta Description | 長度 (120-160 chars)、包含關鍵字 |
| 內容結構 | H2/H3 使用、段落長度、列表 |
| 關鍵字密度 | 目標關鍵字出現率 (1-3%) |
| 可讀性 | 句子長度、被動語態比例 |

### 4. Tool 註冊模式

每個 Tool 檔案遵循統一模式：

```typescript
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

export function registerContentTools(server: McpServer, client: WpApiClient) {
  server.tool(
    "content_list_posts",
    "列出網站文章，支援分頁和篩選",
    {
      page: z.number().optional().default(1),
      per_page: z.number().optional().default(10),
      status: z.enum(["publish", "draft", "pending", "trash"]).optional(),
      search: z.string().optional(),
      categories: z.string().optional(),
      tags: z.string().optional(),
    },
    async (params) => {
      const result = await client.listPosts(params);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }
  );
}
```

## 環境設定 (`.env.example`)

```env
# WordPress 連線設定
WP_BASE_URL=https://your-blog.com
WP_USERNAME=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# MCP Server 設定
LOG_LEVEL=info
MAX_RETRIES=3
REQUEST_TIMEOUT_MS=10000

# SEO 設定
DEFAULT_LANGUAGE=zh-TW
SITEMAP_PING_GOOGLE=false
```

## 安全性設計

1. **認證**：使用 WordPress Application Passwords（非帳密）
2. **傳輸**：所有 API 呼叫走 HTTPS
3. **儲存**：`.env` 檔案不進版控（`.gitignore`）
4. **輸入驗證**：所有 Tool 參數使用 Zod schema 驗證
5. **錯誤處理**：不洩漏內部錯誤細節到 MCP response

## 擴展點

架構設計支援以下擴展，無需修改核心：

1. **新 CMS 支援**：實作新的 API Client（如 `laravel-api-client.ts`），替換注入
2. **新 SEO 規則**：在 `seo-engine/` 新增規則檔案，自動註冊
3. **新 Tool 類別**：在 `tools/` 新增檔案，於 `index.ts` 註冊
4. **新傳輸層**：替換 `StdioServerTransport` 為 HTTP SSE transport
