import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { WpApiClient } from "../client/wp-api-client.js";
import { toMcpError } from "../utils/errors.js";

export function registerAnalyticsTools(server: McpServer, client: WpApiClient) {
  server.tool(
    "analytics_top_posts",
    "取得熱門文章排行（依修改日期排序，可擴展接 GA）",
    {
      limit: z.number().int().min(1).max(50).optional().describe("回傳筆數，預設 10"),
      period: z.enum(["day", "week", "month"]).optional().describe("時間範圍"),
    },
    async ({ limit, period }) => {
      try {
        let after: string | undefined;
        const now = new Date();
        if (period === "day") {
          after = new Date(now.getTime() - 86400000).toISOString();
        } else if (period === "week") {
          after = new Date(now.getTime() - 7 * 86400000).toISOString();
        } else if (period === "month") {
          after = new Date(now.getTime() - 30 * 86400000).toISOString();
        }

        const result = await client.listPosts({
          per_page: limit ?? 10,
          status: "publish",
          orderby: "modified",
          order: "desc",
          after,
        });

        const topPosts = result.items.map((post) => ({
          id: post.id,
          title: post.title.rendered,
          slug: post.slug,
          date: post.date,
          modified: post.modified,
          link: post.link,
        }));

        return {
          content: [{ type: "text", text: JSON.stringify(topPosts, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "analytics_post_stats",
    "取得單篇文章的基本統計資訊",
    {
      id: z.number().int().positive().describe("文章 ID"),
    },
    async ({ id }) => {
      try {
        const post = await client.getPost(id);
        const stats = {
          id: post.id,
          title: post.title.rendered,
          status: post.status,
          date: post.date,
          modified: post.modified,
          author: post.author,
          categories: post.categories,
          tags: post.tags,
          wordCount: post.content.rendered
            .replace(/<[^>]*>/g, "")
            .split(/\s+/)
            .filter(Boolean).length,
        };
        return {
          content: [{ type: "text", text: JSON.stringify(stats, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );
}
