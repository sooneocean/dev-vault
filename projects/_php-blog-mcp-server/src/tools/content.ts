import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { WpApiClient } from "../client/wp-api-client.js";
import { toMcpError } from "../utils/errors.js";

export function registerContentTools(server: McpServer, client: WpApiClient) {
  server.tool(
    "content_list_posts",
    "列出網站文章，支援分頁和篩選條件",
    {
      page: z.number().int().min(1).optional().describe("頁碼，預設 1"),
      per_page: z.number().int().min(1).max(100).optional().describe("每頁筆數，預設 10"),
      status: z.enum(["publish", "draft", "pending", "trash"]).optional().describe("文章狀態篩選"),
      search: z.string().optional().describe("搜尋關鍵字"),
      categories: z.string().optional().describe("分類 ID，逗號分隔"),
      tags: z.string().optional().describe("標籤 ID，逗號分隔"),
    },
    async (params) => {
      try {
        const result = await client.listPosts(params);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "content_get_post",
    "取得單篇文章的完整內容和 meta 資料",
    {
      id: z.number().int().positive().describe("文章 ID"),
    },
    async ({ id }) => {
      try {
        const post = await client.getPost(id);
        return {
          content: [{ type: "text", text: JSON.stringify(post, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "content_create_post",
    "建立新文章，支援標題、內容、狀態、分類和標籤",
    {
      title: z.string().min(1).describe("文章標題"),
      content: z.string().describe("文章內容 (HTML)"),
      status: z.enum(["publish", "draft", "pending", "private"]).optional().describe("發佈狀態"),
      categories: z.array(z.number().int()).optional().describe("分類 ID 陣列"),
      tags: z.array(z.number().int()).optional().describe("標籤 ID 陣列"),
      excerpt: z.string().optional().describe("文章摘要"),
      date: z.string().optional().describe("排程發佈日期 (ISO 8601)"),
    },
    async (params) => {
      try {
        const post = await client.createPost(params);
        return {
          content: [{ type: "text", text: JSON.stringify(post, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "content_update_post",
    "更新文章內容，支援部分更新",
    {
      id: z.number().int().positive().describe("文章 ID"),
      title: z.string().optional().describe("新標題"),
      content: z.string().optional().describe("新內容 (HTML)"),
      status: z.enum(["publish", "draft", "pending", "private", "trash"]).optional().describe("新狀態"),
      categories: z.array(z.number().int()).optional().describe("分類 ID 陣列"),
      tags: z.array(z.number().int()).optional().describe("標籤 ID 陣列"),
      excerpt: z.string().optional().describe("新摘要"),
      date: z.string().optional().describe("新排程日期 (ISO 8601)"),
    },
    async ({ id, ...data }) => {
      try {
        const post = await client.updatePost(id, data);
        return {
          content: [{ type: "text", text: JSON.stringify(post, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "content_delete_post",
    "刪除文章，支援移到回收站或永久刪除",
    {
      id: z.number().int().positive().describe("文章 ID"),
      force: z.boolean().optional().describe("true = 永久刪除，false = 移到回收站"),
    },
    async ({ id, force }) => {
      try {
        const result = await client.deletePost(id, force);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "content_batch_update",
    "批次更新多篇文章的狀態、分類或標籤",
    {
      ids: z.array(z.number().int().positive()).min(1).describe("文章 ID 陣列"),
      status: z.enum(["publish", "draft", "pending", "trash"]).optional().describe("批次設定狀態"),
      categories: z.array(z.number().int()).optional().describe("批次設定分類"),
      tags: z.array(z.number().int()).optional().describe("批次設定標籤"),
    },
    async ({ ids, ...data }) => {
      try {
        const results = await Promise.allSettled(
          ids.map((id) => client.updatePost(id, data)),
        );
        const summary = {
          total: ids.length,
          succeeded: results.filter((r) => r.status === "fulfilled").length,
          failed: results.filter((r) => r.status === "rejected").length,
          results: results.map((r, i) => ({
            id: ids[i],
            status: r.status,
            ...(r.status === "rejected" ? { error: r.reason?.message } : {}),
          })),
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
