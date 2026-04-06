import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { WpApiClient } from "../client/wp-api-client.js";
import { registerContentTools } from "./content.js";
import { registerSeoTools } from "./seo.js";
import { registerTaxonomyTools } from "./taxonomies.js";
import { registerMediaTools } from "./media.js";
import { registerAnalyticsTools } from "./analytics.js";
import { registerSiteTools } from "./site.js";

export function registerAllTools(server: McpServer, client: WpApiClient): void {
  registerContentTools(server, client);
  registerSeoTools(server, client);
  registerTaxonomyTools(server, client);
  registerMediaTools(server, client);
  registerAnalyticsTools(server, client);
  registerSiteTools(server, client);
}
