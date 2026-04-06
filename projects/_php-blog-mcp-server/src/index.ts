import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { getConfig } from "./config.js";
import { setLogLevel, logger } from "./utils/logger.js";
import { WpApiClient } from "./client/wp-api-client.js";
import { registerAllTools } from "./tools/index.js";

async function main() {
  const config = getConfig();
  setLogLevel(config.LOG_LEVEL as "debug" | "info" | "warn" | "error");

  logger.info("Starting php-blog-mcp-server", {
    wpBaseUrl: config.WP_BASE_URL,
    logLevel: config.LOG_LEVEL,
  });

  const wpClient = new WpApiClient({
    baseUrl: config.WP_BASE_URL,
    username: config.WP_USERNAME,
    appPassword: config.WP_APP_PASSWORD,
    maxRetries: config.MAX_RETRIES,
    timeoutMs: config.REQUEST_TIMEOUT_MS,
  });

  const server = new McpServer(
    { name: "php-blog-mcp-server", version: "1.0.0" },
    { capabilities: { tools: {} } },
  );

  registerAllTools(server, wpClient);

  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info("Server connected and ready");
}

main().catch((error) => {
  logger.error("Fatal error", { error: error.message });
  process.exit(1);
});
