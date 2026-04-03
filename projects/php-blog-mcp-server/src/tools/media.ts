import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { WpApiClient } from "../client/wp-api-client.js";
import { toMcpError } from "../utils/errors.js";

export function registerMediaTools(server: McpServer, client: WpApiClient) {
  server.tool(
    "media_list",
    "列出媒體庫檔案",
    {
      page: z.number().int().min(1).optional().describe("頁碼"),
      per_page: z.number().int().min(1).max(100).optional().describe("每頁筆數"),
      media_type: z.enum(["image", "video", "audio", "application"]).optional().describe("媒體類型篩選"),
      mime_type: z.string().optional().describe("MIME type 篩選"),
    },
    async (params) => {
      try {
        const result = await client.listMedia(params);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "media_delete",
    "刪除媒體檔案",
    {
      id: z.number().int().positive().describe("媒體 ID"),
      force: z.boolean().optional().describe("是否永久刪除"),
    },
    async ({ id, force }) => {
      try {
        await client.deleteMedia(id, force);
        return {
          content: [{ type: "text", text: `Media ${id} deleted` }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );
}
