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
 *   rollback   — Restore original post content from NDJSON backup
 *
 * Usage:
 *   node scripts/internal-linker-v2.js --phase fetch-map
 *   node scripts/internal-linker-v2.js --phase propose
 *   node scripts/internal-linker-v2.js --phase inject --dry-run
 *   node scripts/internal-linker-v2.js --phase inject
 *   node scripts/internal-linker-v2.js --phase fix-broken
 *   node scripts/internal-linker-v2.js --phase rollback
 *
 * Env:
 *   WP_BEARER_TOKEN — WordPress.com REST API Bearer token
 *   (or set in .env file)
 *
 * Module usage:
 *   import { fetchMap, generateProposals, injectLinks, fixBrokenLinks, rollbackLinks } from './internal-linker-v2.js';
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import {
  discoverAuth,
  resolveApiBase,
  apiGet as sharedApiGet,
  apiPost as sharedApiPost,
  appendNDJSON,
  readNDJSON,
  sleep,
  ensureDir,
  saveJSON as sharedSaveJSON,
  loadJSON,
  log,
} from "./lib/seo-shared.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Default Config ─────────────────────────────────────────────────────────

const DEFAULT_CONFIG = {
  siteId: 133512998,
  domain: "yololab.net",
  dataDir: path.join(__dirname, "../data"),
  outputDir: path.join(__dirname, "../seo-optimization-output"),
  rootDir: path.join(__dirname, ".."),
  rateLimit: {
    batchSize: 10,
    delayMs: 1500,
    retries: 3,
    backoffMs: 2000,
  },
};

// ─── Internal Helpers (use shared utilities) ────────────────────────────────

function resolveConfig(config = {}) {
  return { ...DEFAULT_CONFIG, ...config };
}

function getApiContext(config) {
  const auth = discoverAuth({ rootDir: config.rootDir });
  if (!auth) {
    throw new Error("No auth found. Set WP_APP_USER+WP_APP_PASS or WP_BEARER_TOKEN in .env");
  }
  const apiBase = resolveApiBase({ siteId: config.siteId, domain: config.domain }, auth);
  return { auth, apiBase };
}

async function _apiGet(endpoint, config) {
  const { auth, apiBase } = getApiContext(config);
  return sharedApiGet(`${apiBase}${endpoint}`, auth.headers, config.rateLimit);
}

async function _apiPost(endpoint, body, config) {
  const { auth, apiBase } = getApiContext(config);
  return sharedApiPost(`${apiBase}${endpoint}`, body, auth.headers, config.rateLimit);
}

// ─── Data Loaders ────────────────────────────────────────────────────────────

function loadTier1(config) {
  const p = path.join(config.dataDir, "tier1-articles.json");
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function loadPillarMap(config) {
  const p = path.join(config.dataDir, "pillar-map.json");
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function loadArticleMap(config) {
  const p = path.join(config.dataDir, "tier1-article-map.json");
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function backupPath(config) {
  return path.join(config.outputDir, "internal-links-backup.ndjson");
}

// ─── Phase: fetch-map ────────────────────────────────────────────────────────

export async function fetchMap(userConfig) {
  const config = resolveConfig(userConfig);
  const tier1 = loadTier1(config);
  const allIds = Object.values(tier1.tier1_articles).flat();
  console.log(`📥 Fetching ${allIds.length} article titles/URLs...`);

  const map = {};
  let done = 0;

  for (let i = 0; i < allIds.length; i += config.rateLimit.batchSize) {
    const batch = allIds.slice(i, i + config.rateLimit.batchSize);

    for (const id of batch) {
      try {
        const post = await _apiGet(`/posts/${id}?_fields=id,title,link,categories`, config);
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

    if (i + config.rateLimit.batchSize < allIds.length) {
      await sleep(config.rateLimit.delayMs);
    }
  }

  // Also fetch pillar pages
  const pillars = loadPillarMap(config);
  for (const [cat, info] of Object.entries(pillars.pillar_pages)) {
    const id = info.article_id;
    if (!map[id]) {
      try {
        const post = await _apiGet(`/posts/${id}?_fields=id,title,link`, config);
        map[id] = { id, title: post.title.rendered, link: post.link, isPillar: true };
      } catch (err) {
        console.log(`\n  ❌ Pillar ${cat} (${id}): ${err.message}`);
      }
      await sleep(500);
    } else {
      map[id].isPillar = true;
    }
  }

  const outPath = path.join(config.dataDir, "tier1-article-map.json");
  sharedSaveJSON(outPath, { generated: new Date().toISOString(), articles: map });
  console.log(`\n📝 Saved to ${outPath}`);
  console.log(`  Total: ${Object.keys(map).length} articles mapped`);

  return { articlesCount: Object.keys(map).length, outputPath: outPath, articles: map };
}

// ─── Phase: propose ──────────────────────────────────────────────────────────

export function generateProposals(userConfig) {
  const config = resolveConfig(userConfig);
  const tier1 = loadTier1(config);
  const pillars = loadPillarMap(config);
  const articleMap = loadArticleMap(config);

  if (!articleMap) {
    throw new Error("Article map not found. Run fetch-map phase first.");
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

  const outPath = path.join(config.outputDir, "proposed-links-v2.json");
  sharedSaveJSON(outPath, {
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

  return { totalArticles: proposals.length, totalLinks: proposals.reduce((s, p) => s + p.links.length, 0), proposals, outputPath: outPath };
}

// ─── Phase: inject ───────────────────────────────────────────────────────────

export function buildRelatedSection(links) {
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

export const RELATED_MARKER = "延伸閱讀";

export async function injectLinks(userConfig, options = {}) {
  const config = resolveConfig(userConfig);
  const dryRun = options.dryRun || false;

  const proposalPath = path.join(config.outputDir, "proposed-links-v2.json");
  if (!fs.existsSync(proposalPath)) {
    throw new Error("Proposals not found. Run propose phase first.");
  }

  const { proposals } = JSON.parse(fs.readFileSync(proposalPath, "utf-8"));
  const statePath = path.join(config.outputDir, "link-inject-state.json");
  const state = fs.existsSync(statePath)
    ? JSON.parse(fs.readFileSync(statePath, "utf-8"))
    : { completed: [], failed: [], skipped: [] };

  const todo = proposals.filter(
    (p) => !state.completed.includes(p.articleId) && !state.skipped.includes(p.articleId)
  );

  const bkPath = backupPath(config);
  console.log(`🔗 Injecting links: ${todo.length} articles (${dryRun ? "DRY RUN" : "LIVE"})`);
  if (!dryRun) console.log(`📦 Backup: ${bkPath}`);
  let success = 0;
  let skip = 0;
  let fail = 0;

  for (let i = 0; i < todo.length; i++) {
    const proposal = todo[i];

    try {
      // Fetch current content
      const post = await _apiGet(`/posts/${proposal.articleId}?_fields=id,content&context=edit`, config);
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
        // Backup original content BEFORE writing (NDJSON for large-file safety)
        appendNDJSON(bkPath, {
          postId: proposal.articleId,
          originalContent: content,
          backedUpAt: new Date().toISOString(),
        });

        // Update post
        await _apiPost(`/posts/${proposal.articleId}`, {
          content: updatedContent,
        }, config);
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
    if (!dryRun && (i + 1) % config.rateLimit.batchSize === 0) {
      sharedSaveJSON(statePath, state);
      await sleep(config.rateLimit.delayMs);
    }
  }

  if (!dryRun) sharedSaveJSON(statePath, state);

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`✅ Success: ${success} | ⏭️ Skipped: ${skip} | ❌ Failed: ${fail}`);

  return { success, skip, fail, backupPath: dryRun ? null : bkPath };
}

// ─── Phase: rollback ────────────────────────────────────────────────────────

export async function rollbackLinks(userConfig) {
  const config = resolveConfig(userConfig);
  const bkPath = backupPath(config);

  if (!fs.existsSync(bkPath)) {
    throw new Error(`No backup file found at ${bkPath}. Nothing to rollback.`);
  }

  console.log(`🔄 Rolling back from ${bkPath}...`);
  let restored = 0;
  let failed = 0;

  for await (const entry of readNDJSON(bkPath)) {
    const { postId, originalContent } = entry;
    if (!postId || originalContent === undefined) {
      console.log(`  ⚠️ Skipping malformed backup entry`);
      continue;
    }

    try {
      await _apiPost(`/posts/${postId}`, { content: originalContent }, config);
      console.log(`  ✅ [${postId}] Restored original content`);
      restored++;
      await sleep(500);
    } catch (err) {
      console.log(`  ❌ [${postId}] Rollback failed: ${err.message}`);
      failed++;
    }
  }

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`🔄 Rollback complete — Restored: ${restored} | Failed: ${failed}`);

  return { restored, failed };
}

// ─── Phase: fix-broken ───────────────────────────────────────────────────────

export const BROKEN_LINK_PATTERN = /<!-- SEO Link: \w+ --><br\s*\/?>\s*<a href="https:\/\/yololab\.net\/article-\d+\/">.*?<\/a><br\s*\/?>\s*/g;

export async function fixBrokenLinks(userConfig) {
  const config = resolveConfig(userConfig);
  const tier1 = loadTier1(config);
  const allIds = Object.values(tier1.tier1_articles).flat();

  console.log(`🔧 Scanning ${allIds.length} articles for broken SEO links...`);

  let fixed = 0;
  let clean = 0;

  for (const id of allIds) {
    try {
      const post = await _apiGet(`/posts/${id}?_fields=id,content&context=edit`, config);
      const content = post.content.raw || post.content.rendered || "";

      // Reset regex lastIndex since it uses the 'g' flag
      BROKEN_LINK_PATTERN.lastIndex = 0;
      if (BROKEN_LINK_PATTERN.test(content)) {
        BROKEN_LINK_PATTERN.lastIndex = 0;
        const cleaned = content.replace(BROKEN_LINK_PATTERN, "");
        await _apiPost(`/posts/${id}`, { content: cleaned }, config);
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

  return { fixed, clean };
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
      await injectLinks(undefined, { dryRun: args.dryRun });
      break;
    case "fix-broken":
      await fixBrokenLinks();
      break;
    case "rollback":
      await rollbackLinks();
      break;
    default:
      console.error(`❌ Unknown phase: ${args.phase}`);
      console.log("Available: fetch-map, propose, inject, fix-broken, rollback");
      process.exit(1);
  }

  console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("✅ Done");
}

// Only run CLI when executed directly (not imported as module)
const isDirectRun = process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url));
if (isDirectRun) {
  main().catch((err) => {
    console.error("❌ Error:", err.message);
    process.exit(1);
  });
}
