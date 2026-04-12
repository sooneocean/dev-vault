#!/usr/bin/env node

/**
 * YOLO LAB Internal Linker v2
 *
 * Batch injects "延伸閱讀" sections into Tier 1 articles.
 * Each article gets: 1 pillar link + 2 category peer links.
 *
 * Phases:
 *   fetch-map  — Build title/URL mapping for all Tier 1 articles
 *   propose    — Generate link proposals (dry-run)
 *   inject     — Append "延伸閱讀" sections to articles
 *   fix-broken — Remove old broken SEO links from articles
 *
 * Usage:
 *   node scripts/internal-linker-v2.js --phase fetch-map
 *   node scripts/internal-linker-v2.js --phase propose
 *   node scripts/internal-linker-v2.js --phase inject --dry-run
 *   node scripts/internal-linker-v2.js --phase inject
 *   node scripts/internal-linker-v2.js --phase fix-broken
 *
 * Env:
 *   WP_BEARER_TOKEN — WordPress.com REST API Bearer token
 *   (or set in .env file)
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Config ──────────────────────────────────────────────────────────────────

const SITE_ID = 133512998;
const API_BASE = `https://public-api.wordpress.com/wp/v2/sites/${SITE_ID}`;
const DATA_DIR = path.join(__dirname, "../data");
const OUTPUT_DIR = path.join(__dirname, "../seo-optimization-output");

const RATE_LIMIT = {
  batchSize: 10,
  delayMs: 1500,
  retries: 3,
  backoffMs: 2000,
};

// ─── Auth ────────────────────────────────────────────────────────────────────
// Supports two auth methods:
//   1. Application Password (Basic auth) — WP_APP_USER + WP_APP_PASS env vars or .env
//   2. Bearer token — WP_BEARER_TOKEN env var, .env, or .mcp.json

function getAuthHeaders() {
  // Try Application Password first (most reliable for batch operations)
  const user = process.env.WP_APP_USER;
  const pass = process.env.WP_APP_PASS;
  if (user && pass) {
    const encoded = Buffer.from(`${user}:${pass}`).toString("base64");
    return { Authorization: `Basic ${encoded}` };
  }

  // Try .env file for Application Password
  const envPath = path.join(__dirname, "../.env");
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, "utf-8");
    const userMatch = envContent.match(/WP_APP_USER=(.+)/);
    const passMatch = envContent.match(/WP_APP_PASS=(.+)/);
    if (userMatch && passMatch) {
      const encoded = Buffer.from(
        `${userMatch[1].trim()}:${passMatch[1].trim()}`
      ).toString("base64");
      return { Authorization: `Basic ${encoded}` };
    }
  }

  // Fallback to Bearer token
  const token = getToken();
  return { Authorization: `Bearer ${token}` };
}

function getToken() {
  if (process.env.WP_BEARER_TOKEN) return process.env.WP_BEARER_TOKEN;

  const envPath = path.join(__dirname, "../.env");
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, "utf-8");
    const match = envContent.match(/WP_BEARER_TOKEN=(.+)/);
    if (match) return match[1].trim();
  }

  const mcpPath = path.join(__dirname, "../.mcp.json");
  if (fs.existsSync(mcpPath)) {
    const mcp = JSON.parse(fs.readFileSync(mcpPath, "utf-8"));
    const auth = mcp.mcpServers?.["wpcom-mcp"]?.headers?.Authorization;
    if (auth) return auth.replace("Bearer ", "");
  }

  console.error(
    "❌ No auth found. Set WP_APP_USER+WP_APP_PASS or WP_BEARER_TOKEN in .env"
  );
  console.error(
    "   Create Application Password: https://yololab.net/wp-admin/profile.php"
  );
  process.exit(1);
}

// ─── API Helpers ─────────────────────────────────────────────────────────────

async function apiGet(endpoint) {
  const headers = getAuthHeaders();
  for (let attempt = 1; attempt <= RATE_LIMIT.retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, { headers });
      if (res.status === 429) {
        const wait = RATE_LIMIT.backoffMs * attempt;
        console.log(`  ⏳ Rate limited, waiting ${wait}ms...`);
        await sleep(wait);
        continue;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      return await res.json();
    } catch (err) {
      if (attempt === RATE_LIMIT.retries) throw err;
      await sleep(RATE_LIMIT.backoffMs * attempt);
    }
  }
}

async function apiPost(endpoint, body) {
  const headers = { ...getAuthHeaders(), "Content-Type": "application/json" };
  for (let attempt = 1; attempt <= RATE_LIMIT.retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
      if (res.status === 429) {
        const wait = RATE_LIMIT.backoffMs * attempt;
        console.log(`  ⏳ Rate limited, waiting ${wait}ms...`);
        await sleep(wait);
        continue;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      return await res.json();
    } catch (err) {
      if (attempt === RATE_LIMIT.retries) throw err;
      await sleep(RATE_LIMIT.backoffMs * attempt);
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ─── Data Loaders ────────────────────────────────────────────────────────────

function loadTier1() {
  const p = path.join(DATA_DIR, "tier1-articles.json");
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function loadPillarMap() {
  const p = path.join(DATA_DIR, "pillar-map.json");
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function loadArticleMap() {
  const p = path.join(DATA_DIR, "tier1-article-map.json");
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function saveJSON(filename, data) {
  const dir = path.dirname(filename);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(filename, JSON.stringify(data, null, 2));
}

// ─── Phase: fetch-map ────────────────────────────────────────────────────────

async function fetchMap() {
  const tier1 = loadTier1();
  const allIds = Object.values(tier1.tier1_articles).flat();
  console.log(`📥 Fetching ${allIds.length} article titles/URLs...`);

  const map = {};
  let done = 0;

  for (let i = 0; i < allIds.length; i += RATE_LIMIT.batchSize) {
    const batch = allIds.slice(i, i + RATE_LIMIT.batchSize);

    for (const id of batch) {
      try {
        const post = await apiGet(`/posts/${id}?_fields=id,title,link,categories`);
        map[id] = {
          id,
          title: post.title.rendered,
          link: post.link,
          categories: post.categories,
        };
        done++;
        process.stdout.write(`\r  ✅ ${done}/${allIds.length}`);
      } catch (err) {
        console.log(`\n  ❌ Failed to fetch post ${id}: ${err.message}`);
        map[id] = { id, title: `[FETCH_FAILED]`, link: null, error: err.message };
      }
      await sleep(500);
    }

    if (i + RATE_LIMIT.batchSize < allIds.length) {
      await sleep(RATE_LIMIT.delayMs);
    }
  }

  // Also fetch pillar pages
  const pillars = loadPillarMap();
  for (const [cat, info] of Object.entries(pillars.pillar_pages)) {
    const id = info.article_id;
    if (!map[id]) {
      try {
        const post = await apiGet(`/posts/${id}?_fields=id,title,link`);
        map[id] = { id, title: post.title.rendered, link: post.link, isPillar: true };
      } catch (err) {
        console.log(`\n  ❌ Pillar ${cat} (${id}): ${err.message}`);
      }
      await sleep(500);
    } else {
      map[id].isPillar = true;
    }
  }

  const outPath = path.join(DATA_DIR, "tier1-article-map.json");
  saveJSON(outPath, { generated: new Date().toISOString(), articles: map });
  console.log(`\n📝 Saved to ${outPath}`);
  console.log(`  Total: ${Object.keys(map).length} articles mapped`);
}

// ─── Phase: propose ──────────────────────────────────────────────────────────

function generateProposals() {
  const tier1 = loadTier1();
  const pillars = loadPillarMap();
  const articleMap = loadArticleMap();

  if (!articleMap) {
    console.error("❌ Run --phase fetch-map first");
    process.exit(1);
  }

  const proposals = [];

  for (const [category, articleIds] of Object.entries(tier1.tier1_articles)) {
    if (!Array.isArray(articleIds) || articleIds.length === 0) continue;

    const pillarInfo = pillars.pillar_pages[category];
    if (!pillarInfo) {
      console.log(`  ⚠️ No pillar for category: ${category}`);
      continue;
    }

    const pillarArticle = articleMap.articles[pillarInfo.article_id];

    for (let i = 0; i < articleIds.length; i++) {
      const articleId = articleIds[i];
      const article = articleMap.articles[articleId];

      if (!article || !article.link) {
        console.log(`  ⚠️ Skipping ${articleId} (no data)`);
        continue;
      }

      // Skip if this IS the pillar page
      if (articleId === pillarInfo.article_id) continue;

      // Pick 2 peers: nearest neighbors in the list (excluding self and pillar)
      const peers = articleIds
        .filter((id) => id !== articleId && id !== pillarInfo.article_id)
        .slice(0, 4) // candidates
        .sort(() => Math.random() - 0.5) // shuffle for variety
        .slice(0, 2);

      const links = [];

      // Pillar link
      if (pillarArticle && pillarArticle.link) {
        links.push({
          targetId: pillarInfo.article_id,
          title: pillarArticle.title,
          url: pillarArticle.link,
          type: "pillar",
        });
      }

      // Peer links
      for (const peerId of peers) {
        const peer = articleMap.articles[peerId];
        if (peer && peer.link) {
          links.push({
            targetId: peerId,
            title: peer.title,
            url: peer.link,
            type: "cluster_peer",
          });
        }
      }

      proposals.push({
        articleId,
        articleTitle: article.title,
        articleUrl: article.link,
        category,
        links,
      });
    }
  }

  const outPath = path.join(OUTPUT_DIR, "proposed-links-v2.json");
  saveJSON(outPath, {
    generated: new Date().toISOString(),
    totalArticles: proposals.length,
    totalLinks: proposals.reduce((sum, p) => sum + p.links.length, 0),
    proposals,
  });

  console.log(`📋 Generated ${proposals.length} proposals with ${proposals.reduce((s, p) => s + p.links.length, 0)} links`);
  console.log(`📝 Saved to ${outPath}`);

  // Preview
  for (const p of proposals.slice(0, 3)) {
    console.log(`\n  📄 [${p.category}] ${p.articleTitle}`);
    for (const l of p.links) {
      console.log(`     → [${l.type}] ${l.title}`);
    }
  }
  if (proposals.length > 3) console.log(`  ... and ${proposals.length - 3} more`);
}

// ─── Phase: inject ───────────────────────────────────────────────────────────

function buildRelatedSection(links) {
  const items = links.map((l) => {
    const prefix = l.type === "pillar" ? "📌 " : "";
    return `<li><a href="${l.url}">${prefix}${l.title}</a></li>`;
  });

  return [
    `\n<hr class="wp-block-separator has-alpha-channel-opacity"/>`,
    `<h3 class="wp-block-heading">延伸閱讀</h3>`,
    `<ul class="wp-block-list">`,
    ...items,
    `</ul>`,
  ].join("\n");
}

const RELATED_MARKER = "延伸閱讀";

async function injectLinks(dryRun) {
  const proposalPath = path.join(OUTPUT_DIR, "proposed-links-v2.json");
  if (!fs.existsSync(proposalPath)) {
    console.error("❌ Run --phase propose first");
    process.exit(1);
  }

  const { proposals } = JSON.parse(fs.readFileSync(proposalPath, "utf-8"));
  const statePath = path.join(OUTPUT_DIR, "link-inject-state.json");
  const state = fs.existsSync(statePath)
    ? JSON.parse(fs.readFileSync(statePath, "utf-8"))
    : { completed: [], failed: [], skipped: [] };

  const todo = proposals.filter(
    (p) => !state.completed.includes(p.articleId) && !state.skipped.includes(p.articleId)
  );

  console.log(`🔗 Injecting links: ${todo.length} articles (${dryRun ? "DRY RUN" : "LIVE"})`);
  let success = 0;
  let skip = 0;
  let fail = 0;

  for (let i = 0; i < todo.length; i++) {
    const proposal = todo[i];

    try {
      // Fetch current content
      const post = await apiGet(`/posts/${proposal.articleId}?_fields=id,content&context=edit`);
      const content = post.content.raw || post.content.rendered || "";

      // Check if already has "延伸閱讀"
      if (content.includes(RELATED_MARKER)) {
        console.log(`  ⏭️ [${proposal.articleId}] Already has 延伸閱讀, skipping`);
        state.skipped.push(proposal.articleId);
        skip++;
        continue;
      }

      // Build new section
      const relatedSection = buildRelatedSection(proposal.links);
      const updatedContent = content + relatedSection;

      if (dryRun) {
        console.log(`  📋 [${proposal.articleId}] Would append ${proposal.links.length} links`);
        for (const l of proposal.links) {
          console.log(`     → [${l.type}] ${l.title}`);
        }
      } else {
        // Update post
        await apiPost(`/posts/${proposal.articleId}`, {
          content: updatedContent,
        });
        console.log(`  ✅ [${proposal.articleId}] Injected ${proposal.links.length} links`);
        state.completed.push(proposal.articleId);
      }

      success++;
      await sleep(500);
    } catch (err) {
      console.log(`  ❌ [${proposal.articleId}] ${err.message}`);
      state.failed.push({ id: proposal.articleId, error: err.message });
      fail++;
    }

    // Save state periodically
    if (!dryRun && (i + 1) % RATE_LIMIT.batchSize === 0) {
      saveJSON(statePath, state);
      await sleep(RATE_LIMIT.delayMs);
    }
  }

  if (!dryRun) saveJSON(statePath, state);

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`✅ Success: ${success} | ⏭️ Skipped: ${skip} | ❌ Failed: ${fail}`);
}

// ─── Phase: fix-broken ───────────────────────────────────────────────────────

const BROKEN_LINK_PATTERN = /<!-- SEO Link: \w+ --><br\s*\/?>\s*<a href="https:\/\/yololab\.net\/article-\d+\/">.*?<\/a><br\s*\/?>\s*/g;

async function fixBrokenLinks() {
  const tier1 = loadTier1();
  const allIds = Object.values(tier1.tier1_articles).flat();

  console.log(`🔧 Scanning ${allIds.length} articles for broken SEO links...`);

  let fixed = 0;
  let clean = 0;

  for (const id of allIds) {
    try {
      const post = await apiGet(`/posts/${id}?_fields=id,content&context=edit`);
      const content = post.content.raw || post.content.rendered || "";

      if (BROKEN_LINK_PATTERN.test(content)) {
        const cleaned = content.replace(BROKEN_LINK_PATTERN, "");
        await apiPost(`/posts/${id}`, { content: cleaned });
        console.log(`  🔧 [${id}] Removed broken SEO links`);
        fixed++;
      } else {
        clean++;
      }
      await sleep(500);
    } catch (err) {
      console.log(`  ❌ [${id}] ${err.message}`);
    }
  }

  console.log(`\n✅ Fixed: ${fixed} | Clean: ${clean}`);
}

// ─── CLI ─────────────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = { phase: "propose", dryRun: false };

  for (let i = 0; i < args.length; i++) {
    const key = args[i].replace(/^--/, "");
    if (key === "phase" && args[i + 1]) parsed.phase = args[++i];
    if (key === "dry-run") parsed.dryRun = true;
  }
  return parsed;
}

async function main() {
  const args = parseArgs();

  console.log("🔗 YOLO LAB Internal Linker v2");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log(`Phase: ${args.phase}`);
  if (args.dryRun) console.log("Mode: DRY RUN");
  console.log("");

  switch (args.phase) {
    case "fetch-map":
      await fetchMap();
      break;
    case "propose":
      generateProposals();
      break;
    case "inject":
      await injectLinks(args.dryRun);
      break;
    case "fix-broken":
      await fixBrokenLinks();
      break;
    default:
      console.error(`❌ Unknown phase: ${args.phase}`);
      console.log("Available: fetch-map, propose, inject, fix-broken");
      process.exit(1);
  }

  console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("✅ Done");
}

main().catch((err) => {
  console.error("❌ Error:", err.message);
  process.exit(1);
});
