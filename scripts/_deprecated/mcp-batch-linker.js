#!/usr/bin/env node

/**
 * MCP Batch Internal Linker
 *
 * Uses the WordPress.com MCP server directly to batch inject
 * "延伸閱讀" sections into Tier 1 articles.
 *
 * This bypasses the REST API auth issue by connecting to the same
 * MCP SSE endpoint that Claude Code uses.
 *
 * Usage:
 *   node scripts/mcp-batch-linker.js --dry-run    # Preview changes
 *   node scripts/mcp-batch-linker.js               # Execute injection
 *   node scripts/mcp-batch-linker.js --fix-broken  # Remove broken SEO links only
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Config ──────────────────────────────────────────────────────────────────

const SITE_ID = "133512998";
const DATA_DIR = path.join(__dirname, "../data");
const OUTPUT_DIR = path.join(__dirname, "../seo-optimization-output");
const RELATED_MARKER = "延伸閱讀";
const BROKEN_LINK_PATTERN =
  /<!-- SEO Link: \w+ -->\s*(?:<br\s*\/?>)?\s*<a href="https:\/\/yololab\.net\/article-\d+\/">.*?<\/a>\s*(?:<br\s*\/?>)?\s*/g;

// ─── MCP Client ─────────────────────────────────────────────────────────────

function getMcpConfig() {
  const mcpPath = path.join(__dirname, "../.mcp.json");
  const mcp = JSON.parse(fs.readFileSync(mcpPath, "utf-8"));
  const server = mcp.mcpServers["wpcom-mcp"];
  return { url: server.url, headers: server.headers };
}

async function createMcpClient() {
  const config = getMcpConfig();
  const transport = new StreamableHTTPClientTransport(new URL(config.url), {
    requestInit: { headers: config.headers },
  });
  const client = new Client({ name: "batch-linker", version: "1.0.0" });
  await client.connect(transport);
  console.log("✅ Connected to WordPress MCP server");
  return client;
}

async function mcpCall(client, tool, params) {
  const result = await client.callTool({ name: tool, arguments: params });
  // MCP returns content array with text
  const text = result.content
    ?.map((c) => (c.type === "text" ? c.text : ""))
    .join("");
  return JSON.parse(text || "{}");
}

// ─── Data Loaders ───────────────────────────────────────────────────────────

function loadProposals() {
  const p = path.join(OUTPUT_DIR, "proposed-links-v2.json");
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function loadState() {
  const p = path.join(OUTPUT_DIR, "link-inject-state.json");
  if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, "utf-8"));
  return { completed: [], failed: [], skipped: [] };
}

function saveState(state) {
  const p = path.join(OUTPUT_DIR, "link-inject-state.json");
  fs.writeFileSync(p, JSON.stringify(state, null, 2));
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function buildRelatedSection(links) {
  const items = links
    .map((l) => {
      const prefix = l.type === "pillar" ? "📌 " : "";
      return `<li>${prefix}<a href="${l.url}">${l.title}</a></li>`;
    })
    .join("\n");

  return `\n<hr class="wp-block-separator has-alpha-channel-opacity"/>\n<h3 class="wp-block-heading">延伸閱讀</h3>\n<ul class="wp-block-list">\n${items}\n</ul>`;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const fixBrokenOnly = args.includes("--fix-broken");

  const client = await createMcpClient();

  if (fixBrokenOnly) {
    await fixBrokenLinks(client, dryRun);
  } else {
    await injectLinks(client, dryRun);
  }

  await client.close();
}

async function injectLinks(client, dryRun) {
  const { proposals } = loadProposals();
  const state = loadState();

  const todo = proposals.filter(
    (p) =>
      !state.completed.includes(p.articleId) &&
      !state.skipped.includes(p.articleId)
  );

  console.log(
    `\n🔗 Processing ${todo.length} articles (${dryRun ? "DRY RUN" : "LIVE"})\n`
  );

  let success = 0,
    skip = 0,
    fail = 0;

  for (let i = 0; i < todo.length; i++) {
    const proposal = todo[i];
    const label = `[${i + 1}/${todo.length}] ${proposal.articleId}`;

    try {
      // Fetch current content
      const postData = await mcpCall(
        client,
        "wpcom-mcp-content-authoring",
        {
          action: "execute",
          operation: "posts.get",
          wpcom_site: SITE_ID,
          params: {
            id: proposal.articleId,
            context: "edit",
            include_fields: ["id", "content"],
          },
        }
      );

      const content = postData.data?.content || "";

      // Check if already has 延伸閱讀
      if (content.includes(RELATED_MARKER)) {
        console.log(`  ⏭️ ${label} — already has 延伸閱讀`);
        state.skipped.push(proposal.articleId);
        skip++;
        saveState(state);
        continue;
      }

      // Remove broken links if present
      let cleanContent = content;
      const hasBroken = BROKEN_LINK_PATTERN.test(content);
      if (hasBroken) {
        BROKEN_LINK_PATTERN.lastIndex = 0; // reset regex state
        cleanContent = content.replace(BROKEN_LINK_PATTERN, "");
        console.log(`  🔧 ${label} — removing broken SEO links`);
      }

      // Build related section
      const relatedSection = buildRelatedSection(proposal.links);
      const updatedContent = cleanContent + relatedSection;

      if (dryRun) {
        console.log(
          `  📋 ${label} [${proposal.category}] — would add ${proposal.links.length} links${hasBroken ? " + fix broken" : ""}`
        );
        for (const l of proposal.links) {
          console.log(`     → [${l.type}] ${l.title.slice(0, 50)}...`);
        }
        success++;
      } else {
        // Update post
        await mcpCall(client, "wpcom-mcp-content-authoring", {
          action: "execute",
          operation: "posts.update",
          wpcom_site: SITE_ID,
          params: {
            id: proposal.articleId,
            content: { raw: updatedContent },
            include_fields: ["id", "link"],
            user_confirmed: "batch internal link injection",
          },
        });

        console.log(
          `  ✅ ${label} [${proposal.category}] — ${proposal.links.length} links injected${hasBroken ? " + broken fixed" : ""}`
        );
        state.completed.push(proposal.articleId);
        success++;
        saveState(state);
      }

      // Rate limit: 1s between updates
      await sleep(1000);
    } catch (err) {
      console.log(`  ❌ ${label} — ${err.message}`);
      state.failed.push({ id: proposal.articleId, error: err.message });
      fail++;
      saveState(state);
      await sleep(2000); // back off on error
    }
  }

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(
    `✅ Success: ${success} | ⏭️ Skipped: ${skip} | ❌ Failed: ${fail}`
  );
  console.log(`Total completed: ${state.completed.length}`);
}

async function fixBrokenLinks(client, dryRun) {
  const tier1 = JSON.parse(
    fs.readFileSync(path.join(DATA_DIR, "tier1-articles.json"), "utf-8")
  );
  const allIds = Object.values(tier1.tier1_articles).flat();

  console.log(
    `\n🔧 Scanning ${allIds.length} articles for broken SEO links (${dryRun ? "DRY RUN" : "LIVE"})\n`
  );

  let fixed = 0,
    clean = 0;

  for (let i = 0; i < allIds.length; i++) {
    const id = allIds[i];
    try {
      const postData = await mcpCall(
        client,
        "wpcom-mcp-content-authoring",
        {
          action: "execute",
          operation: "posts.get",
          wpcom_site: SITE_ID,
          params: { id, context: "edit", include_fields: ["id", "content"] },
        }
      );

      const content = postData.data?.content || "";
      BROKEN_LINK_PATTERN.lastIndex = 0;

      if (BROKEN_LINK_PATTERN.test(content)) {
        BROKEN_LINK_PATTERN.lastIndex = 0;
        if (dryRun) {
          console.log(`  📋 [${id}] Would remove broken SEO links`);
        } else {
          const cleaned = content.replace(BROKEN_LINK_PATTERN, "");
          await mcpCall(client, "wpcom-mcp-content-authoring", {
            action: "execute",
            operation: "posts.update",
            wpcom_site: SITE_ID,
            params: {
              id,
              content: { raw: cleaned },
              include_fields: ["id"],
              user_confirmed: "fix broken SEO links",
            },
          });
          console.log(`  🔧 [${id}] Fixed`);
        }
        fixed++;
      } else {
        clean++;
      }

      await sleep(500);
    } catch (err) {
      console.log(`  ❌ [${id}] ${err.message}`);
    }
  }

  console.log(`\n🔧 Fixed: ${fixed} | ✅ Clean: ${clean}`);
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
