import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { WpApiClient } from "../client/wp-api-client.js";
import { toMcpError } from "../utils/errors.js";

export function registerSiteTools(server: McpServer, client: WpApiClient) {
  server.tool(
    "site_get_settings",
    "取得網站基本設定（標題、描述、時區、永久連結結構等）",
    {},
    async () => {
      try {
        const settings = await client.getSettings();
        return {
          content: [{ type: "text", text: JSON.stringify(settings, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );

  server.tool(
    "site_update_settings",
    "更新網站設定",
    {
      title: z.string().optional().describe("網站標題"),
      description: z.string().optional().describe("網站描述"),
      timezone: z.string().optional().describe("時區"),
      language: z.string().optional().describe("語言"),
    },
    async (params) => {
      try {
        const settings = await client.updateSettings(params);
        return {
          content: [{ type: "text", text: JSON.stringify(settings, null, 2) }],
        };
      } catch (error) {
        return toMcpError(error);
      }
    },
  );
}
