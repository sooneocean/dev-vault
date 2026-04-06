# php-blog-mcp-server

MCP Server for PHP blog website (WordPress) — 讓 AI 助手直接操作你的部落格網站，自動化內容管理與 SEO 優化。

## Quick Start

```bash
cp .env.example .env    # 填入 WordPress 站點資訊
pnpm install
pnpm run build
pnpm start              # 啟動 MCP Server (stdio)
```

## Architecture

```
AI Agent (Claude) → MCP Protocol → php-blog-mcp-server → WordPress REST API
```

## 17 MCP Tools

| Category | Tools |
|----------|-------|
| **Content** | `content_list_posts` `content_get_post` `content_create_post` `content_update_post` `content_delete_post` `content_batch_update` |
| **SEO** | `seo_analyze_content` `seo_generate_meta` `seo_generate_sitemap` `seo_generate_schema` `seo_health_check` |
| **Taxonomies** | `taxonomies_list_categories` `taxonomies_manage_categories` `taxonomies_list_tags` `taxonomies_manage_tags` |
| **Media** | `media_list` `media_delete` |
| **Analytics** | `analytics_top_posts` `analytics_post_stats` |
| **Site** | `site_get_settings` `site_update_settings` |

## Claude Desktop Config

```json
{
  "mcpServers": {
    "php-blog": {
      "command": "node",
      "args": ["path/to/php-blog-mcp-server/dist/index.js"],
      "env": {
        "WP_BASE_URL": "https://your-blog.com",
        "WP_USERNAME": "admin",
        "WP_APP_PASSWORD": "xxxx xxxx xxxx xxxx xxxx xxxx"
      }
    }
  }
}
```

## Scripts

```bash
pnpm run dev      # Watch mode
pnpm test         # Run tests
pnpm run build    # Compile TypeScript
pnpm run lint     # Lint code
pnpm run format   # Format code
```

## Detailed Docs

→ [使用說明.md](./使用說明.md) — 完整安裝、設定、使用範例、疑難排解

→ [spec/](./spec/) — SDD 規格文件 (Vision / Requirements / Design / Tasks)

## Tech Stack

TypeScript · Node.js ≥ 18 · MCP SDK · Axios · Zod · Vitest

## License

MIT
