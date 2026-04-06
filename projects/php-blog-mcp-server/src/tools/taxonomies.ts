import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { WpApiClient } from "../client/wp-api-client.js";
import { toMcpError } from "../utils/errors.js";

export function registerTaxonomyTools(server: McpServer, client: WpApiClient) {
  server.tool(
    "taxonomies_list_categories",
    "列出所有分類，含父子關係",
    {
      page: z.number().int().min(1).optional().describe("頁碼"),
      per_page: z.number().int().min(1).max(100).optional().describe("每頁筆數"),
      search: z.string().optional().describe("搜尋關鍵字"),
    },
    async (params) => {
      try {
        const result = await client.listCategories(params);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "taxonomies_manage_categories",
    "建立、更新或刪除分類",
    {
      action: z.enum(["create", "update", "delete"]).describe("操作類型"),
      id: z.number().int().positive().optional().describe("分類 ID (update/delete 時必填)"),
      name: z.string().optional().describe("分類名稱"),
      slug: z.string().optional().describe("分類 slug"),
      parent: z.number().int().optional().describe("父分類 ID"),
      description: z.string().optional().describe("分類描述"),
    },
    async ({ action, id, ...data }) => {
      try {
        switch (action) {
          case "create": {
            if (!data.name) throw new Error("name is required for create");
            const cat = await client.createCategory(data as { name: string; slug?: string; parent?: number; description?: string });
            return { content: [{ type: "text", text: JSON.stringify(cat, null, 2) }] };
          }
          case "update": {
            if (!id) throw new Error("id is required for update");
            const cat = await client.updateCategory(id, data);
            return { content: [{ type: "text", text: JSON.stringify(cat, null, 2) }] };
          }
          case "delete": {
            if (!id) throw new Error("id is required for delete");
            await client.deleteCategory(id);
            return { content: [{ type: "text", text: `Category ${id} deleted` }] };
          }
        }
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "taxonomies_list_tags",
    "列出所有標籤",
    {
      page: z.number().int().min(1).optional().describe("頁碼"),
      per_page: z.number().int().min(1).max(100).optional().describe("每頁筆數"),
      search: z.string().optional().describe("搜尋關鍵字"),
    },
    async (params) => {
      try {
        const result = await client.listTags(params);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "taxonomies_manage_tags",
    "建立、更新或刪除標籤",
    {
      action: z.enum(["create", "update", "delete"]).describe("操作類型"),
      id: z.number().int().positive().optional().describe("標籤 ID (update/delete 時必填)"),
      name: z.string().optional().describe("標籤名稱"),
      slug: z.string().optional().describe("標籤 slug"),
      description: z.string().optional().describe("標籤描述"),
    },
    async ({ action, id, ...data }) => {
      try {
        switch (action) {
          case "create": {
            if (!data.name) throw new Error("name is required for create");
            const tag = await client.createTag(data as { name: string; slug?: string; description?: string });
            return { content: [{ type: "text", text: JSON.stringify(tag, null, 2) }] };
          }
          case "update": {
            if (!id) throw new Error("id is required for update");
            const tag = await client.updateTag(id, data);
            return { content: [{ type: "text", text: JSON.stringify(tag, null, 2) }] };
          }
          case "delete": {
            if (!id) throw new Error("id is required for delete");
            await client.deleteTag(id);
            return { content: [{ type: "text", text: `Tag ${id} deleted` }] };
          }
        }
      } catch (error) {
        return toMcpError(error);
      }
    },
  );
}
