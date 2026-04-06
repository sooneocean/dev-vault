import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { WpApiClient } from "../client/wp-api-client.js";
import { toMcpError } from "../utils/errors.js";
import { analyzeContent } from "../seo-engine/analyzer.js";
import { generateMeta } from "../seo-engine/meta-generator.js";
import { generateSitemapXml, generateArticleSchema } from "../seo-engine/schema-generator.js";

export function registerSeoTools(server: McpServer, client: WpApiClient) {
  server.tool(
    "seo_analyze_content",
    "分析文章內容的 SEO 評分，回傳 0-100 分數及各維度改善建議",
    {
      title: z.string().describe("文章標題"),
      content: z.string().describe("文章內容 (HTML)"),
      metaDescription: z.string().optional().describe("Meta description"),
      focusKeyword: z.string().optional().describe("目標關鍵字"),
      language: z.string().optional().describe("語言代碼，預設 zh-TW"),
    },
    async (params) => {
      try {
        const score = analyzeContent(params);
        return {
          content: [{ type: "text", text: JSON.stringify(score, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "seo_generate_meta",
    "自動生成 SEO meta tags (title, description, Open Graph, Twitter Card)",
    {
      title: z.string().describe("文章標題"),
      content: z.string().describe("文章內容 (HTML)"),
      focusKeyword: z.string().optional().describe("目標關鍵字"),
      siteName: z.string().optional().describe("網站名稱"),
    },
    async (params) => {
      try {
        const meta = generateMeta(
          params.title,
          params.content,
          params.focusKeyword,
          params.siteName,
        );
        return {
          content: [{ type: "text", text: JSON.stringify(meta, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "seo_generate_sitemap",
    "生成 XML sitemap（含所有已發佈文章）",
    {
      baseUrl: z.string().url().describe("網站根 URL"),
      perPage: z.number().int().min(1).max(100).optional().describe("每頁取得文章數"),
    },
    async ({ baseUrl, perPage }) => {
      try {
        const allPosts: Awaited<ReturnType<typeof client.listPosts>>["items"] = [];
        let page = 1;
        let totalPages = 1;

        while (page <= totalPages) {
          const result = await client.listPosts({
            page,
            per_page: perPage ?? 100,
            status: "publish",
          });
          allPosts.push(...result.items);
          totalPages = result.totalPages;
          page++;
        }

        const xml = generateSitemapXml(baseUrl, allPosts);
        return {
          content: [{ type: "text", text: xml }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "seo_generate_schema",
    "生成 Article 結構化資料 (JSON-LD Schema.org)",
    {
      postId: z.number().int().positive().describe("文章 ID"),
      baseUrl: z.string().url().describe("網站根 URL"),
      authorName: z.string().optional().describe("作者名稱"),
      siteName: z.string().optional().describe("網站名稱"),
    },
    async ({ postId, baseUrl, authorName, siteName }) => {
      try {
        const post = await client.getPost(postId);
        const schema = generateArticleSchema(post, baseUrl, authorName, siteName);
        return {
          content: [{ type: "text", text: JSON.stringify(schema, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "seo_health_check",
    "執行全站 SEO 健康掃描，檢查缺失 meta、broken links 等",
    {
      maxPosts: z.number().int().min(1).max(500).optional().describe("掃描文章數上限"),
    },
    async ({ maxPosts }) => {
      try {
        const limit = maxPosts ?? 100;
        const result = await client.listPosts({ per_page: limit, status: "publish" });
        const issues: Array<{ postId: number; title: string; problems: string[] }> = [];

        for (const post of result.items) {
          const problems: string[] = [];

          if (!post.yoast_meta?.yoast_wpseo_metadesc) {
            problems.push("Missing meta description");
          }
          if (!post.yoast_meta?.yoast_wpseo_title) {
            problems.push("Missing SEO title");
          }
          if (!post.excerpt?.rendered?.trim()) {
            problems.push("Missing excerpt");
          }
          if (post.title.rendered.length < 30) {
            problems.push("Title too short (< 30 chars)");
          }
          if (post.categories.length === 0) {
            problems.push("No category assigned");
          }

          if (problems.length > 0) {
            issues.push({
              postId: post.id,
              title: post.title.rendered,
              problems,
            });
          }
        }

        const summary = {
          totalScanned: result.items.length,
          healthyPosts: result.items.length - issues.length,
          postsWithIssues: issues.length,
          issues,
        };

        return {
          content: [{ type: "text", text: JSON.stringify(summary, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );
}
