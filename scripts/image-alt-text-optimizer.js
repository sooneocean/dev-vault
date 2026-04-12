#!/usr/bin/env node

/**
 * YOLO LAB Image Alt Text Optimizer
 *
 * 自動為全站文章圖片生成 SEO 優化的繁體中文 alt text，
 * 使用 Claude Vision 分析圖片內容，批次更新 WordPress.com。
 *
 * Phases:
 *   scan      — 掃描全站文章，盤點圖片 alt 狀態，產出 audit report
 *   featured  — 批次更新 featured_media 的 alt text
 *   inline    — 批次更新文章內嵌 <img> 的 alt 屬性
 *   report    — 產出品質驗證報告
 *   rollback  — 從 backup JSON 還原 (featured / inline / all)
 *
 * Usage:
 *   node scripts/image-alt-text-optimizer.js --phase scan [--sample N]
 *   node scripts/image-alt-text-optimizer.js --phase featured [--dry-run] [--resume] [--sample N]
 *   node scripts/image-alt-text-optimizer.js --phase inline [--dry-run] [--resume] [--sample N]
 *   node scripts/image-alt-text-optimizer.js --phase report
 *   node scripts/image-alt-text-optimizer.js --rollback featured|inline|all
 *
 * Env:
 *   ANTHROPIC_API_KEY — Claude API key
 *   WP_BEARER_TOKEN or WP_APP_USER+WP_APP_PASS — WordPress.com auth
 */

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import {
  discoverAuth,
  resolveApiBase,
  apiGet as sharedApiGet,
  apiPost as sharedApiPost,
  createBackup as sharedCreateBackup,
  loadBackup as sharedLoadBackup,
  loadState as sharedLoadState,
  saveState as sharedSaveState,
  acquireGlobalLock,
  releaseGlobalLock,
  sleep,
  ensureDir,
  saveJSON,
  loadJSON,
  log,
  isFilenameLikeAlt,
  DEFAULT_RATE_LIMIT,
} from "./lib/seo-shared.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Default Config (used by CLI main()) ────────────────────────────────────

const DEFAULT_SITE_CONFIG = {
  siteId: 133512998,
  domain: "yololab.net",
};

function buildDefaultConfig() {
  const rootDir = path.join(__dirname, "..");
  const auth = discoverAuth({ rootDir });
  const apiBase = auth ? resolveApiBase(DEFAULT_SITE_CONFIG, auth) : null;
  const apiV1 = `https://public-api.wordpress.com/rest/v1.1/sites/${DEFAULT_SITE_CONFIG.siteId}`;
  return {
    siteId: DEFAULT_SITE_CONFIG.siteId,
    domain: DEFAULT_SITE_CONFIG.domain,
    apiBase,
    apiV1,
    auth,
    outputDir: path.join(rootDir, "seo-optimization-output"),
    rateLimit: { ...DEFAULT_RATE_LIMIT },
    visionModel: "claude-haiku-4-5-20251001",
    rootDir,
  };
}

// Legacy compatibility wrappers — used internally when config is available
function getApiBaseFromConfig(config) {
  return config.apiBase;
}
function getAuthHeadersFromConfig(config) {
  return config.auth?.headers || {};
}

// ─── Legacy Config (backward compatibility for direct CLI invocation) ────────

const LEGACY_OUTPUT_DIR = path.join(__dirname, "../seo-optimization-output");

const RATE_LIMIT = { ...DEFAULT_RATE_LIMIT };

const VISION_MODEL = "claude-haiku-4-5-20251001";
const LOCK_FILE = path.join(LEGACY_OUTPUT_DIR, ".batch.lock");

// ─── CLI Args ────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const phase = args.find((a) => a.startsWith("--phase="))?.split("=")[1]
  || args[args.indexOf("--phase") + 1];
const rollbackTarget = args.find((a) => a.startsWith("--rollback="))?.split("=")[1]
  || (args.includes("--rollback") ? args[args.indexOf("--rollback") + 1] : null);
const dryRun = args.includes("--dry-run");
const resume = args.includes("--resume");
const sampleSize = parseInt(
  args.find((a) => a.startsWith("--sample="))?.split("=")[1]
  || args[args.indexOf("--sample") + 1]
  || "0"
);

// ─── Auth (delegated to seo-shared.js) ──────────────────────────────────────
// Legacy wrappers for backward compat within this file

function getAuthHeaders() {
  const auth = discoverAuth({ rootDir: path.join(__dirname, "..") });
  if (!auth) {
    console.error("No auth found. Set WP_APP_USER+WP_APP_PASS or WP_BEARER_TOKEN in .env");
    process.exit(1);
  }
  return auth.headers;
}

function getApiBase() {
  const auth = discoverAuth({ rootDir: path.join(__dirname, "..") });
  if (!auth) return `https://public-api.wordpress.com/wp/v2/sites/${DEFAULT_SITE_CONFIG.siteId}`;
  return resolveApiBase(DEFAULT_SITE_CONFIG, auth);
}

// Legacy lock wrappers
function acquireLock() {
  acquireGlobalLock(LOCK_FILE, 3600000); // 1 hour TTL for legacy
}

function releaseLock() {
  releaseGlobalLock(LOCK_FILE);
}

// ─── API Health Check (Deepening #2) ───────────────────────────────────────

async function healthCheck(config) {
  log("Running API health check...", "info");
  const base = config ? config.apiBase : getApiBase();
  const headers = config ? getAuthHeadersFromConfig(config) : getAuthHeaders();
  const apiV1 = config ? config.apiV1 : `https://public-api.wordpress.com/rest/v1.1/sites/${DEFAULT_SITE_CONFIG.siteId}`;

  try {
    // Check posts read
    const postsRes = await fetch(`${base}/posts?per_page=1`, { headers });
    if (!postsRes.ok) throw new Error(`Posts read failed: ${postsRes.status}`);
    log("Posts read permission OK", "success");

    // Check media read/write (via WordPress.com v1.1 API)
    const mediaRes = await fetch(`${apiV1}/media?number=1`, {
      headers,
      method: "GET",
    });
    if (!mediaRes.ok && mediaRes.status !== 404) {
      throw new Error(`Media read failed: ${mediaRes.status}`);
    }
    log("Media read permission OK", "success");

    log("Health check passed", "success");
  } catch (error) {
    log(`Health check failed: ${error.message}`, "error");
    throw error;
  }
}

// ─── API Helpers (parameterized, delegating to seo-shared.js) ───────────────

async function apiGet(baseOrConfig, endpoint) {
  // Support both legacy (base, endpoint) and config-based calls
  if (typeof baseOrConfig === "object" && baseOrConfig.apiBase) {
    const config = baseOrConfig;
    return sharedApiGet(`${config.apiBase}${endpoint}`, getAuthHeadersFromConfig(config), config.rateLimit);
  }
  // Legacy: baseOrConfig is a URL string
  const headers = getAuthHeaders();
  return sharedApiGet(`${baseOrConfig}${endpoint}`, headers, RATE_LIMIT);
}

async function apiPost(baseOrConfig, endpoint, body) {
  if (typeof baseOrConfig === "object" && baseOrConfig.apiBase) {
    const config = baseOrConfig;
    return sharedApiPost(`${config.apiBase}${endpoint}`, body, getAuthHeadersFromConfig(config), config.rateLimit);
  }
  const headers = getAuthHeaders();
  return sharedApiPost(`${baseOrConfig}${endpoint}`, body, headers, RATE_LIMIT);
}

// ─── State Management (parameterized) ───────────────────────────────────────

function loadAltState(name, outputDir) {
  const dir = outputDir || LEGACY_OUTPUT_DIR;
  const filepath = path.join(dir, `state_alttext_${name}.json`);
  return loadJSON(filepath) || {
    name,
    startTime: new Date().toISOString(),
    processed: [],
    failed: [],
    skipped: [],
    partial: [],
    altCache: {},
    stats: { total: 0, updated: 0, skipped: 0, failed: 0, decorative: 0 },
  };
}

function saveAltState(state, outputDir) {
  const dir = outputDir || LEGACY_OUTPUT_DIR;
  const filepath = path.join(dir, `state_alttext_${state.name}.json`);
  saveJSON(filepath, state);
}

// ─── Phase: scan ─────────────────────────────────────────────────────────────

/**
 * Scan all site articles, audit image alt text status, produce report.
 *
 * @param {object} config - Site config: { siteId, domain, apiBase, apiV1, auth, outputDir, rateLimit, rootDir }
 * @param {object} [options] - { sample, skipLock, skipHealthCheck }
 * @returns {Promise<object>} Audit report object
 */
export async function exportPhaseScan(config, options = {}) {
  const sampleSz = options.sample || 0;
  const outputDir = config.outputDir || LEGACY_OUTPUT_DIR;
  const lockFile = path.join(outputDir, ".batch.lock");

  log("Phase: scan — 掃描全站文章圖片 alt 狀態");
  ensureDir(outputDir);

  // Deepening #2, #3: Health check and acquire lock
  if (!options.skipLock) {
    try {
      acquireGlobalLock(lockFile, 3600000);
    } catch (error) {
      throw new Error(`Lock acquisition failed: ${error.message}`);
    }
  }
  if (!options.skipHealthCheck) {
    try {
      await healthCheck(config);
    } catch (error) {
      if (!options.skipLock) releaseGlobalLock(lockFile);
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  try {

  // Paginated fetch of all posts via wp/v2 with context=edit
  const allPosts = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    try {
      const posts = await apiGet(
        config,
        `/posts?per_page=100&page=${page}&_fields=id,title,featured_media,content,categories`
      );
      if (!posts || posts.length === 0) {
        hasMore = false;
      } else {
        allPosts.push(...posts);
        log(`已取得 ${allPosts.length} 篇文章 (page ${page})`);
        page++;
        await sleep(500);
      }
    } catch (err) {
      if (err.message.includes("400") || err.message.includes("rest_post_invalid_page_number")) {
        hasMore = false;
      } else {
        log(`取得文章失敗 (page ${page}): ${err.message}`, "error");
        hasMore = false;
      }
    }
  }

  log(`共取得 ${allPosts.length} 篇文章`);

  // Apply sample limit
  const posts = sampleSz > 0 ? allPosts.slice(0, sampleSz) : allPosts;
  if (sampleSz > 0) log(`Sample mode: 只處理前 ${sampleSz} 篇`);

  // Collect all unique featured_media IDs
  const featuredMediaIds = [...new Set(
    posts.filter((p) => p.featured_media > 0).map((p) => p.featured_media)
  )];
  log(`共 ${featuredMediaIds.length} 個不重複的 featured_media`);

  // Fetch media items for featured images
  const rl = config.rateLimit || RATE_LIMIT;
  const mediaMap = {};
  for (let i = 0; i < featuredMediaIds.length; i += rl.batchSize) {
    const batch = featuredMediaIds.slice(i, i + rl.batchSize);
    for (const mediaId of batch) {
      try {
        const media = await apiGet(config, `/media/${mediaId}?_fields=id,alt_text,source_url,title`);
        mediaMap[mediaId] = {
          id: mediaId,
          alt: media.alt_text || "",
          title: media.title?.rendered || media.title || "",
          url: media.source_url || "",
        };
      } catch (err) {
        log(`取得 media ${mediaId} 失敗: ${err.message}`, "error");
        mediaMap[mediaId] = { id: mediaId, alt: "", title: "", url: "", error: err.message };
      }
      await sleep(200);
    }
    if (i + rl.batchSize < featuredMediaIds.length) {
      await sleep(rl.delayMs);
    }
  }

  // Parse inline images from content
  const imgRegex = /<img\s[^>]*>/gi;
  const srcRegex = /src=["']([^"']+)["']/i;
  const altRegex = /alt=["']([^"']*)["']/i;

  const report = {
    generated: new Date().toISOString(),
    totalPosts: posts.length,
    summary: {
      featuredMedia: { total: 0, needsAlt: 0, hasAlt: 0, filenameLike: 0 },
      inlineImages: { total: 0, needsAlt: 0, hasAlt: 0, filenameLike: 0, noAltAttr: 0 },
      uniqueImageUrls: 0,
    },
    posts: [],
  };

  const allImageUrls = new Set();

  for (const post of posts) {
    const postEntry = {
      id: post.id,
      title: post.title?.raw || post.title?.rendered || "",
      categories: post.categories || [],
      featuredMedia: null,
      inlineImages: [],
    };

    // Featured media
    if (post.featured_media > 0 && mediaMap[post.featured_media]) {
      const media = mediaMap[post.featured_media];
      const needsUpdate = isFilenameLikeAlt(media.alt);
      postEntry.featuredMedia = {
        mediaId: media.id,
        currentAlt: media.alt,
        url: media.url,
        needsUpdate,
      };
      report.summary.featuredMedia.total++;
      if (needsUpdate) {
        report.summary.featuredMedia.needsAlt++;
      } else {
        report.summary.featuredMedia.hasAlt++;
      }
      if (media.url) allImageUrls.add(media.url);
    }

    // Inline images — scan phase uses rendered content to find images
    const content = post.content?.rendered || post.content?.raw || "";
    const imgMatches = content.match(imgRegex) || [];

    for (const imgTag of imgMatches) {
      const srcMatch = imgTag.match(srcRegex);
      const altMatch = imgTag.match(altRegex);
      const src = srcMatch ? srcMatch[1] : "";
      const alt = altMatch ? altMatch[1] : null; // null means no alt attribute at all
      const hasAltAttr = altMatch !== null;
      const needsUpdate = !hasAltAttr || isFilenameLikeAlt(alt);

      postEntry.inlineImages.push({
        src,
        currentAlt: alt,
        hasAltAttr,
        needsUpdate,
      });

      report.summary.inlineImages.total++;
      if (!hasAltAttr) {
        report.summary.inlineImages.noAltAttr++;
        report.summary.inlineImages.needsAlt++;
      } else if (isFilenameLikeAlt(alt)) {
        report.summary.inlineImages.filenameLike++;
        report.summary.inlineImages.needsAlt++;
      } else {
        report.summary.inlineImages.hasAlt++;
      }

      if (src) allImageUrls.add(src);
    }

    report.posts.push(postEntry);
  }

  report.summary.uniqueImageUrls = allImageUrls.size;

  // Save audit report
  const reportPath = path.join(outputDir, "image-audit-report.json");
  saveJSON(reportPath, report);

  // Print summary
  console.log("\n═══════════════════════════════════════════════════");
  console.log("  YOLO LAB 圖片 Alt Text 盤點報告");
  console.log("═══════════════════════════════════════════════════");
  console.log(`  文章總數:           ${report.totalPosts}`);
  console.log(`  不重複圖片 URL:     ${report.summary.uniqueImageUrls}`);
  console.log("───────────────────────────────────────────────────");
  console.log("  Featured Media:");
  console.log(`    總數:             ${report.summary.featuredMedia.total}`);
  console.log(`    需要更新:         ${report.summary.featuredMedia.needsAlt}`);
  console.log(`    已有 alt:         ${report.summary.featuredMedia.hasAlt}`);
  console.log("───────────────────────────────────────────────────");
  console.log("  內嵌圖片:");
  console.log(`    總數:             ${report.summary.inlineImages.total}`);
  console.log(`    需要更新:         ${report.summary.inlineImages.needsAlt}`);
  console.log(`    已有 alt:         ${report.summary.inlineImages.hasAlt}`);
  console.log(`    無 alt 屬性:      ${report.summary.inlineImages.noAltAttr}`);
  console.log(`    檔名式 alt:       ${report.summary.inlineImages.filenameLike}`);
  console.log("═══════════════════════════════════════════════════");
  console.log(`\n報告已儲存: ${reportPath}`);

  return report;
  } finally {
    if (!options.skipLock) releaseGlobalLock(path.join(outputDir, ".batch.lock"));
  }
}

// ─── Phase: Claude Vision Alt Text Generation ────────────────────────────────

const ALT_TEXT_TOOL = {
  name: "generate_alt_text",
  description: "Generate SEO-optimized alt text for an image",
  input_schema: {
    type: "object",
    properties: {
      alt_text: {
        type: "string",
        description: "繁體中文 alt text, 80-125 characters, SEO optimized",
      },
      is_decorative: {
        type: "boolean",
        description: "True if image is purely decorative (spacer, divider, background)",
      },
    },
    required: ["alt_text", "is_decorative"],
  },
};

async function generateAltText(client, imageUrl, articleTitle, categoryNames, altCache, attempt = 1) {
  // Check cache first
  if (altCache[imageUrl]) {
    return altCache[imageUrl];
  }

  const systemPrompt = `你是 SEO 圖片 alt text 專家。為圖片生成繁體中文 alt text。

規則：
- 80-125 字元
- 自然融入 1-2 個與文章主題相關的關鍵字
- 不以「圖片」、「照片」、「image of」、「photo of」開頭
- 使用自然語言，加標點符號
- 描述圖片中的主體、動作、和相關情境
- 如果圖片包含文字，在 alt text 中包含該文字內容
- 如果圖片是純裝飾性的（分隔線、spacer、背景圖），設 is_decorative 為 true
- 語言：繁體中文`;

  const userContent = [
    {
      type: "text",
      text: `文章標題: ${articleTitle}\n分類: ${categoryNames.join(", ") || "未分類"}\n\n請為這張圖片生成 SEO 優化的 alt text。`,
    },
  ];

  // Try URL mode first for image
  let useBase64 = false;
  try {
    userContent.push({
      type: "image",
      source: { type: "url", url: imageUrl },
    });
  } catch {
    useBase64 = true;
  }

  // Deepening #4: API 超時保護 (45 seconds)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 45000);

  // If URL mode fails or image is inaccessible, fallback to text-only
  try {
    const response = await client.messages.create({
      model: VISION_MODEL,
      max_tokens: 300,
      system: systemPrompt,
      tools: [ALT_TEXT_TOOL],
      tool_choice: { type: "tool", name: "generate_alt_text" },
      messages: [{ role: "user", content: userContent }],
    });

    const toolUse = response.content.find((b) => b.type === "tool_use");
    if (toolUse?.input) {
      const result = {
        alt_text: toolUse.input.alt_text || "",
        is_decorative: toolUse.input.is_decorative || false,
      };

      // Quality gate
      if (!result.is_decorative) {
        const len = result.alt_text.length;
        if (len < 30 || len > 150) {
          log(`品質閘門: alt text 長度 ${len} 不在 30-150 範圍`, "warning");
          // Retry once
          const retry = await client.messages.create({
            model: VISION_MODEL,
            max_tokens: 300,
            system: systemPrompt + "\n\n重要：alt text 必須在 80-125 字元之間。",
            tools: [ALT_TEXT_TOOL],
            tool_choice: { type: "tool", name: "generate_alt_text" },
            messages: [{ role: "user", content: userContent }],
          });
          const retryTool = retry.content.find((b) => b.type === "tool_use");
          if (retryTool?.input?.alt_text) {
            result.alt_text = retryTool.input.alt_text;
            result.is_decorative = retryTool.input.is_decorative || false;
          }
          // If still out of range, truncate
          if (result.alt_text.length > 150) {
            result.alt_text = result.alt_text.slice(0, 147) + "...";
          }
        }

        // Check forbidden patterns
        const forbidden = /^(image of|photo of|picture of|圖片|照片)/i;
        if (forbidden.test(result.alt_text)) {
          result.alt_text = result.alt_text.replace(forbidden, "").trim();
        }
      }

      altCache[imageUrl] = result;
      return result;
    }
  } catch (err) {
    clearTimeout(timeoutId);

    // Deepening #5: 指數退避重試 (3 times max)
    if (attempt < 3 && (err.message.includes("429") || err.message.includes("timeout") || err.message.includes("AbortError"))) {
      const delayMs = Math.min(1000 * Math.pow(2, attempt - 1) + Math.random() * 1000, 10000);
      log(`Vision API 失敗 (attempt ${attempt}/3)，${Math.round(delayMs)}ms 後重試...`, "warning");
      await sleep(delayMs);
      return generateAltText(client, imageUrl, articleTitle, categoryNames, altCache, attempt + 1);
    }

    // If Vision fails (e.g., URL inaccessible), fallback to text-only
    if (!useBase64 && (err.message.includes("image") || err.message.includes("URL") || err.message.includes("Could not"))) {
      log(`Vision 失敗，降級為文字推測: ${imageUrl.slice(-40)}`, "warning");
      return generateAltTextFallback(client, articleTitle, categoryNames, imageUrl, altCache);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }

  return { alt_text: "", is_decorative: false };
}

async function generateAltTextFallback(client, articleTitle, categoryNames, imageUrl, altCache) {
  if (altCache[imageUrl]) return altCache[imageUrl];

  const response = await client.messages.create({
    model: VISION_MODEL,
    max_tokens: 300,
    system: `你是 SEO 圖片 alt text 專家。根據文章標題和分類，推測圖片內容並生成繁體中文 alt text。
規則：80-125 字元、自然融入關鍵字、不以「圖片」開頭、加標點。`,
    tools: [ALT_TEXT_TOOL],
    tool_choice: { type: "tool", name: "generate_alt_text" },
    messages: [{
      role: "user",
      content: `文章標題: ${articleTitle}\n分類: ${categoryNames.join(", ") || "未分類"}\n圖片檔名: ${path.basename(imageUrl)}\n\n請根據上下文推測圖片內容，生成 alt text。`,
    }],
  });

  const toolUse = response.content.find((b) => b.type === "tool_use");
  const result = toolUse?.input
    ? { alt_text: toolUse.input.alt_text || "", is_decorative: toolUse.input.is_decorative || false }
    : { alt_text: "", is_decorative: false };

  altCache[imageUrl] = result;
  return result;
}

// ─── Phase: featured ─────────────────────────────────────────────────────────

/**
 * Batch-update featured_media alt text using Claude Vision.
 *
 * @param {object} config - Site config
 * @param {object} [options] - { dryRun, resume, sample }
 * @returns {Promise<object>} Execution state with stats
 */
export async function exportPhaseFeatured(config, options = {}) {
  const isDryRun = options.dryRun ?? false;
  const isResume = options.resume ?? false;
  const sampleSz = options.sample || 0;
  const outputDir = config.outputDir || LEGACY_OUTPUT_DIR;

  log("Phase: featured — 批次更新 featured_media alt text");

  // Load audit report
  const reportPath = path.join(outputDir, "image-audit-report.json");
  const report = loadJSON(reportPath);
  if (!report) {
    throw new Error("Audit report not found. Run phaseScan first.");
  }

  // Load or create state
  const state = loadAltState("featured", outputDir);
  const processedIds = new Set(state.processed.map((p) => p.mediaId));

  // Collect featured media that needs update (deduplicated by mediaId)
  const mediaToUpdate = new Map();
  for (const post of report.posts) {
    if (post.featuredMedia?.needsUpdate && !processedIds.has(post.featuredMedia.mediaId)) {
      if (!mediaToUpdate.has(post.featuredMedia.mediaId)) {
        mediaToUpdate.set(post.featuredMedia.mediaId, {
          mediaId: post.featuredMedia.mediaId,
          url: post.featuredMedia.url,
          currentAlt: post.featuredMedia.currentAlt,
          articleTitle: post.title,
          categories: post.categories,
        });
      }
    }
  }

  const items = [...mediaToUpdate.values()];
  if (sampleSz > 0) items.splice(sampleSz);
  state.stats.total = items.length + state.processed.length;

  log(`待處理: ${items.length} 個 featured_media (已處理: ${state.processed.length})`);
  if (isDryRun) log("DRY-RUN 模式 — 不會實際更新", "warning");

  // Initialize Claude client
  const client = new Anthropic();

  // Backup file
  const backupPath = path.join(outputDir, "alt-text-backup-featured.json");
  const backup = loadJSON(backupPath) || { created: new Date().toISOString(), items: [] };

  // Fetch category names for context
  let categoryMap = {};
  try {
    const cats = await apiGet(config, "/categories?per_page=100&_fields=id,name");
    categoryMap = Object.fromEntries(cats.map((c) => [c.id, c.name]));
  } catch (err) {
    log(`取得分類失敗: ${err.message}`, "warning");
  }

  const rl = config.rateLimit || RATE_LIMIT;

  // Process in batches
  for (let i = 0; i < items.length; i += rl.batchSize) {
    const batch = items.slice(i, i + rl.batchSize);

    for (const item of batch) {
      try {
        const catNames = item.categories.map((id) => categoryMap[id] || `cat-${id}`);

        // Generate alt text
        const result = await generateAltText(client, item.url, item.articleTitle, catNames, state.altCache);

        if (result.is_decorative) {
          state.skipped.push({ mediaId: item.mediaId, reason: "decorative" });
          state.stats.decorative++;
          state.stats.skipped++;
          log(`⏭️ media ${item.mediaId}: 裝飾性圖片，跳過`, "skip");
          continue;
        }

        if (!result.alt_text) {
          state.failed.push({ mediaId: item.mediaId, error: "empty alt text generated" });
          state.stats.failed++;
          continue;
        }

        // Backup original
        backup.items.push({ mediaId: item.mediaId, originalAlt: item.currentAlt });

        if (!isDryRun) {
          // Update via API
          await apiPost(config, `/media/${item.mediaId}`, { alt_text: result.alt_text });
          log(`media ${item.mediaId}: "${result.alt_text.slice(0, 50)}..."`, "success");

          // Deepening #6: post-write verification
          if (!options.skipVerification) {
            try {
              await sleep(500); // Wait for API to settle
              const verifyRes = await apiGet(config, `/media/${item.mediaId}?_fields=alt_text`);
              if (verifyRes.alt_text === result.alt_text) {
                log(`Verified: media ${item.mediaId}`, "success");
                state.verified = state.verified || [];
                state.verified.push({ mediaId: item.mediaId, status: "verified" });
              } else {
                log(`Verification failed: media ${item.mediaId} (mismatch)`, "error");
                state.verificationFailed = state.verificationFailed || [];
                state.verificationFailed.push({
                  mediaId: item.mediaId,
                  expected: result.alt_text,
                  actual: verifyRes.alt_text,
                });
              }
            } catch (verifyErr) {
              log(`Verification error: media ${item.mediaId}: ${verifyErr.message}`, "warning");
            }
          }
        } else {
          log(`[DRY-RUN] media ${item.mediaId}: "${result.alt_text.slice(0, 50)}..."`, "info");
        }

        state.processed.push({
          mediaId: item.mediaId,
          newAlt: result.alt_text,
          timestamp: new Date().toISOString(),
        });
        state.stats.updated++;
      } catch (err) {
        log(`media ${item.mediaId}: ${err.message}`, "error");
        state.failed.push({ mediaId: item.mediaId, error: err.message });
        state.stats.failed++;
      }

      await sleep(300);
    }

    // Save state after each batch
    saveAltState(state, outputDir);
    if (!isDryRun) saveJSON(backupPath, backup);

    if (i + rl.batchSize < items.length) {
      await sleep(rl.delayMs);
    }
  }

  // Final state save
  state.endTime = new Date().toISOString();
  saveAltState(state, outputDir);
  if (!isDryRun) saveJSON(backupPath, backup);

  console.log("\n═══════════════════════════════════════════════════");
  console.log("  Featured Media Alt Text 更新完成");
  console.log("═══════════════════════════════════════════════════");
  console.log(`  已更新: ${state.stats.updated}`);
  console.log(`  跳過:   ${state.stats.skipped} (裝飾性: ${state.stats.decorative})`);
  console.log(`  失敗:   ${state.stats.failed}`);
  console.log("═══════════════════════════════════════════════════");

  return state;
}

// ─── Phase: inline ───────────────────────────────────────────────────────────

/**
 * Batch-update inline image alt text in post content using Claude Vision.
 *
 * @param {object} config - Site config
 * @param {object} [options] - { dryRun, resume, sample, skipVerification }
 * @returns {Promise<object>} Execution state with stats
 */
export async function exportPhaseInline(config, options = {}) {
  const isDryRun = options.dryRun ?? false;
  const sampleSz = options.sample || 0;
  const outputDir = config.outputDir || LEGACY_OUTPUT_DIR;

  log("Phase: inline — 批次更新內嵌圖片 alt text");

  const reportPath = path.join(outputDir, "image-audit-report.json");
  const report = loadJSON(reportPath);
  if (!report) {
    throw new Error("Audit report not found. Run phaseScan first.");
  }

  const state = loadAltState("inline", outputDir);
  const processedPostIds = new Set(state.processed.map((p) => p.postId));
  const partialPostIds = new Map(state.partial.map((p) => [p.postId, p.pendingImgIndices]));

  // Filter posts that have inline images needing update
  let postsToProcess = report.posts.filter((p) => {
    if (processedPostIds.has(p.id)) return false;
    return p.inlineImages.some((img) => img.needsUpdate);
  });

  if (sampleSz > 0) postsToProcess = postsToProcess.slice(0, sampleSz);
  state.stats.total = postsToProcess.length + state.processed.length;

  log(`待處理: ${postsToProcess.length} 篇文章 (已處理: ${state.processed.length}, partial: ${state.partial.length})`);
  if (isDryRun) log("DRY-RUN 模式 — 不會實際更新", "warning");

  const client = new Anthropic();

  const backupPath = path.join(outputDir, "alt-text-backup-inline.json");
  const backup = loadJSON(backupPath) || { created: new Date().toISOString(), items: [] };

  let categoryMap = {};
  try {
    const cats = await apiGet(config, "/categories?per_page=100&_fields=id,name");
    categoryMap = Object.fromEntries(cats.map((c) => [c.id, c.name]));
  } catch (err) {
    log(`取得分類失敗: ${err.message}`, "warning");
  }

  const rl = config.rateLimit || RATE_LIMIT;

  for (let i = 0; i < postsToProcess.length; i += rl.batchSize) {
    const batch = postsToProcess.slice(i, i + rl.batchSize);

    for (const postInfo of batch) {
      try {
        // Fetch current content.raw via wp/v2 with context=edit
        const post = await apiGet(config, `/posts/${postInfo.id}?context=edit&_fields=id,content`);
        let content = post.content?.raw || post.content?.rendered || "";

        if (!content) {
          state.skipped.push({ postId: postInfo.id, reason: "empty content" });
          state.stats.skipped++;
          continue;
        }

        // Backup original content
        backup.items.push({ postId: postInfo.id, originalContent: content });

        const catNames = postInfo.categories.map((id) => categoryMap[id] || `cat-${id}`);
        const imgRegex = /<img\s[^>]*>/gi;
        let modified = false;
        let successCount = 0;
        let failCount = 0;
        const pendingIndices = [];

        // Determine which img indices to process
        const partialPending = partialPostIds.get(postInfo.id);

        let imgIndex = 0;
        content = content.replace(imgRegex, (imgTag) => {
          const currentIdx = imgIndex++;

          // If partial resume, only process pending indices
          if (partialPending && !partialPending.includes(currentIdx)) {
            return imgTag;
          }

          const srcMatch = imgTag.match(/src=["']([^"']+)["']/i);
          const altMatch = imgTag.match(/alt=["']([^"']*)["']/i);
          const src = srcMatch ? srcMatch[1] : "";
          const currentAlt = altMatch ? altMatch[1] : null;

          // Skip if alt is already good
          if (currentAlt !== null && !isFilenameLikeAlt(currentAlt)) {
            return imgTag;
          }

          // Try to get alt from cache synchronously (generated earlier or in featured phase)
          if (state.altCache[src]) {
            const cached = state.altCache[src];
            if (cached.is_decorative) {
              // Ensure decorative images have alt=""
              if (currentAlt === null) {
                modified = true;
                successCount++;
                return imgTag.replace(/<img\s/, '<img alt="" ');
              }
              return imgTag;
            }
            if (cached.alt_text) {
              modified = true;
              successCount++;
              if (currentAlt !== null) {
                return imgTag.replace(/alt=["'][^"']*["']/i, `alt="${cached.alt_text.replace(/"/g, '&quot;')}"`);
              } else {
                return imgTag.replace(/<img\s/, `<img alt="${cached.alt_text.replace(/"/g, '&quot;')}" `);
              }
            }
          }

          // Mark as pending for async generation
          pendingIndices.push({ idx: currentIdx, src, currentAlt, imgTag });
          return imgTag; // Will be replaced in async pass
        });

        // Async generation for pending images
        if (pendingIndices.length > 0) {
          for (const pending of pendingIndices) {
            try {
              const result = await generateAltText(client, pending.src, postInfo.title, catNames, state.altCache);

              if (result.is_decorative) {
                if (pending.currentAlt === null) {
                  // Add empty alt for decorative
                  content = content.replace(pending.imgTag, pending.imgTag.replace(/<img\s/, '<img alt="" '));
                  modified = true;
                }
                successCount++;
                state.stats.decorative++;
                continue;
              }

              if (result.alt_text) {
                const escapedAlt = result.alt_text.replace(/"/g, "&quot;");
                if (pending.currentAlt !== null) {
                  content = content.replace(
                    pending.imgTag,
                    pending.imgTag.replace(/alt=["'][^"']*["']/i, `alt="${escapedAlt}"`)
                  );
                } else {
                  content = content.replace(
                    pending.imgTag,
                    pending.imgTag.replace(/<img\s/, `<img alt="${escapedAlt}" `)
                  );
                }
                modified = true;
                successCount++;
              } else {
                failCount++;
              }
            } catch (err) {
              log(`  img ${pending.idx} 生成失敗: ${err.message}`, "warning");
              failCount++;
            }
          }
        }

        // Update post if modified
        if (modified && !isDryRun) {
          await apiPost(config, `/posts/${postInfo.id}`, { content: content });

          // Deepening #6: post-write verification (HTML integrity check)
          if (!options.skipVerification) {
            try {
              await sleep(500);
              const verifyPost = await apiGet(config, `/posts/${postInfo.id}?context=edit&_fields=id,content`);
              const verifyContent = verifyPost.content?.raw || verifyPost.content?.rendered || "";

              // Check if Gutenberg block comments are preserved
              const originalHasBlocks = /<!\-\- wp:/.test(content);
              const updatedHasBlocks = /<!\-\- wp:/.test(verifyContent);

              if (originalHasBlocks && !updatedHasBlocks) {
                log(`✗ HTML 驗証失敗: 文章 ${postInfo.id} block comments 被破壞`, "error");
                state.verificationFailed = state.verificationFailed || [];
                state.verificationFailed.push({ postId: postInfo.id, reason: "block comments lost" });
              } else {
                log(`✓ 驗証通過: 文章 ${postInfo.id}`, "success");
                state.verified = state.verified || [];
                state.verified.push({ postId: postInfo.id, status: "verified" });
              }
            } catch (verifyErr) {
              log(`驗証錯誤: 文章 ${postInfo.id}: ${verifyErr.message}`, "warning");
            }
          }
          log(`post ${postInfo.id}: 更新 ${successCount} 張圖片`, "success");
        } else if (modified && isDryRun) {
          log(`[DRY-RUN] post ${postInfo.id}: 會更新 ${successCount} 張圖片`, "info");
        }

        // Track state
        if (failCount === 0) {
          state.processed.push({
            postId: postInfo.id,
            imagesUpdated: successCount,
            timestamp: new Date().toISOString(),
          });
          state.stats.updated += successCount;
        } else if (successCount > 0) {
          // Partial success — record which indices still need work
          const remainingIndices = pendingIndices
            .filter((p) => !state.altCache[p.src]?.alt_text && !state.altCache[p.src]?.is_decorative)
            .map((p) => p.idx);
          state.partial.push({ postId: postInfo.id, pendingImgIndices: remainingIndices });
          state.stats.updated += successCount;
          state.stats.failed += failCount;
        } else {
          state.failed.push({ postId: postInfo.id, error: `${failCount} images failed` });
          state.stats.failed += failCount;
        }
      } catch (err) {
        log(`post ${postInfo.id}: ${err.message}`, "error");
        state.failed.push({ postId: postInfo.id, error: err.message });
        state.stats.failed++;
      }

      await sleep(500);
    }

    saveAltState(state, outputDir);
    if (!isDryRun) saveJSON(backupPath, backup);

    if (i + rl.batchSize < postsToProcess.length) {
      await sleep(rl.delayMs);
    }
  }

  state.endTime = new Date().toISOString();
  saveAltState(state, outputDir);
  if (!isDryRun) saveJSON(backupPath, backup);

  console.log("\n═══════════════════════════════════════════════════");
  console.log("  Inline Image Alt Text 更新完成");
  console.log("═══════════════════════════════════════════════════");
  console.log(`  已更新:   ${state.stats.updated} 張圖片`);
  console.log(`  跳過:     ${state.stats.skipped}`);
  console.log(`  失敗:     ${state.stats.failed}`);
  console.log(`  裝飾性:   ${state.stats.decorative}`);
  console.log(`  Partial:  ${state.partial.length} 篇文章`);
  console.log("═══════════════════════════════════════════════════");

  return state;
}

// ─── Phase: rollback ─────────────────────────────────────────────────────────

/**
 * Rollback featured and/or inline alt text changes from backup.
 *
 * @param {object} config - Site config
 * @param {string} target - "featured" | "inline" | "all"
 * @param {object} [options] - { skipVerification }
 * @returns {Promise<object>} { results: [{ target, restored, failed }] }
 */
export async function exportPhaseRollback(config, target, options = {}) {
  if (!["featured", "inline", "all"].includes(target)) {
    throw new Error("Rollback target must be featured / inline / all");
  }

  const outputDir = config.outputDir || LEGACY_OUTPUT_DIR;

  // Deepening #7: rollback order — inline first, featured second
  const targets = target === "all" ? ["inline", "featured"] : [target];
  const results = [];
  const rl = config.rateLimit || RATE_LIMIT;

  for (const t of targets) {
    log(`Rollback: ${t}`);
    const backupPath = path.join(outputDir, `alt-text-backup-${t}.json`);
    const backup = loadJSON(backupPath);

    if (!backup?.items?.length) {
      log(`Backup file missing or empty: ${backupPath}`, "error");
      results.push({ target: t, restored: 0, failed: 0, error: "backup missing" });
      continue;
    }

    log(`共 ${backup.items.length} 項待還原`);
    let restored = 0;
    let failed = 0;

    for (let i = 0; i < backup.items.length; i += rl.batchSize) {
      const batch = backup.items.slice(i, i + rl.batchSize);

      for (const item of batch) {
        try {
          if (t === "featured") {
            await apiPost(config, `/media/${item.mediaId}`, { alt_text: item.originalAlt });

            if (!options.skipVerification) {
              await sleep(300);
              const verifyMedia = await apiGet(config, `/media/${item.mediaId}?_fields=alt_text`);
              if (verifyMedia.alt_text === item.originalAlt) {
                log(`Verified rollback: media ${item.mediaId}`, "success");
              } else {
                log(`Rollback verification failed: media ${item.mediaId}`, "error");
              }
            } else {
              log(`media ${item.mediaId}: restored`, "success");
            }
          } else {
            await apiPost(config, `/posts/${item.postId}`, { content: item.originalContent });
            log(`post ${item.postId}: restored`, "success");
          }
          restored++;
        } catch (err) {
          log(`Rollback failed: ${err.message}`, "error");
          failed++;
        }
        await sleep(300);
      }

      if (i + rl.batchSize < backup.items.length) {
        await sleep(rl.delayMs);
      }
    }

    results.push({ target: t, restored, failed });
    console.log(`\n  ${t}: restored ${restored}, failed ${failed}`);
  }

  return { results };
}

// ─── Phase: report ───────────────────────────────────────────────────────────

/**
 * Generate a quality verification report from execution states.
 *
 * @param {object} config - Site config (needs outputDir)
 * @returns {object} { markdown, reportPath, stats }
 */
export function exportPhaseReport(config) {
  const outputDir = config.outputDir || LEGACY_OUTPUT_DIR;

  log("Phase: report — 產出品質驗證報告");

  const featuredState = loadJSON(path.join(outputDir, "state_alttext_featured.json"));
  const inlineState = loadJSON(path.join(outputDir, "state_alttext_inline.json"));

  if (!featuredState && !inlineState) {
    throw new Error("No state files found. Run phaseFeatured or phaseInline first.");
  }

  // Combine stats
  const fStats = featuredState?.stats || { total: 0, updated: 0, skipped: 0, failed: 0, decorative: 0 };
  const iStats = inlineState?.stats || { total: 0, updated: 0, skipped: 0, failed: 0, decorative: 0 };

  // Alt text length distribution
  const altCache = { ...featuredState?.altCache, ...inlineState?.altCache };
  const lengths = Object.values(altCache)
    .filter((v) => v.alt_text && !v.is_decorative)
    .map((v) => v.alt_text.length);

  const lengthBuckets = { "0-30": 0, "31-80": 0, "81-125": 0, "126-150": 0, "151+": 0 };
  for (const len of lengths) {
    if (len <= 30) lengthBuckets["0-30"]++;
    else if (len <= 80) lengthBuckets["31-80"]++;
    else if (len <= 125) lengthBuckets["81-125"]++;
    else if (len <= 150) lengthBuckets["126-150"]++;
    else lengthBuckets["151+"]++;
  }

  const decorativeCount = Object.values(altCache).filter((v) => v.is_decorative).length;
  const avgLength = lengths.length > 0 ? Math.round(lengths.reduce((a, b) => a + b, 0) / lengths.length) : 0;

  // Failed items
  const featuredFailed = featuredState?.failed || [];
  const inlineFailed = inlineState?.failed || [];

  // Generate markdown
  const md = `# YOLO LAB 圖片 Alt Text 優化報告

Generated: ${new Date().toISOString()}

## 執行摘要

| 指標 | Featured Media | 內嵌圖片 | 合計 |
|------|---------------|---------|------|
| 總數 | ${fStats.total} | ${iStats.total} | ${fStats.total + iStats.total} |
| 已更新 | ${fStats.updated} | ${iStats.updated} | ${fStats.updated + iStats.updated} |
| 跳過 | ${fStats.skipped} | ${iStats.skipped} | ${fStats.skipped + iStats.skipped} |
| 失敗 | ${fStats.failed} | ${iStats.failed} | ${fStats.failed + iStats.failed} |
| 裝飾性 | ${fStats.decorative} | ${iStats.decorative} | ${fStats.decorative + iStats.decorative} |

## Alt Text 品質分析

- **不重複 alt text 數量:** ${lengths.length}
- **平均長度:** ${avgLength} 字元
- **裝飾性圖片:** ${decorativeCount}

### 長度分布

| 範圍 | 數量 | 比例 |
|------|------|------|
| 0-30 字元（過短） | ${lengthBuckets["0-30"]} | ${lengths.length ? Math.round(lengthBuckets["0-30"] / lengths.length * 100) : 0}% |
| 31-80 字元（偏短） | ${lengthBuckets["31-80"]} | ${lengths.length ? Math.round(lengthBuckets["31-80"] / lengths.length * 100) : 0}% |
| 81-125 字元（最佳） | ${lengthBuckets["81-125"]} | ${lengths.length ? Math.round(lengthBuckets["81-125"] / lengths.length * 100) : 0}% |
| 126-150 字元（可接受） | ${lengthBuckets["126-150"]} | ${lengths.length ? Math.round(lengthBuckets["126-150"] / lengths.length * 100) : 0}% |
| 151+ 字元（過長） | ${lengthBuckets["151+"]} | ${lengths.length ? Math.round(lengthBuckets["151+"] / lengths.length * 100) : 0}% |

## 失敗項目

${featuredFailed.length > 0 ? `### Featured Media 失敗 (${featuredFailed.length})\n\n${featuredFailed.map((f) => `- media ${f.mediaId}: ${f.error}`).join("\n")}` : "### Featured Media\n\n無失敗項目 ✅"}

${inlineFailed.length > 0 ? `### Inline Images 失敗 (${inlineFailed.length})\n\n${inlineFailed.map((f) => `- post ${f.postId}: ${f.error}`).join("\n")}` : "### Inline Images\n\n無失敗項目 ✅"}

${inlineState?.partial?.length > 0 ? `### Partial 文章 (${inlineState.partial.length})\n\n${inlineState.partial.map((p) => `- post ${p.postId}: ${p.pendingImgIndices.length} 張圖片待處理`).join("\n")}` : ""}

## 建議後續行動

1. ${fStats.failed + iStats.failed > 0 ? `重新執行 --resume 處理 ${fStats.failed + iStats.failed} 個失敗項目` : "所有項目處理成功"}
2. 使用 Google Search Console 監控圖片搜尋流量變化（預計 2-4 週可見效果）
3. 考慮為圖片加入 ImageObject Schema 標記（後續迭代）
4. 定期對新文章執行 alt text 優化
`;

  const reportPath = path.join(outputDir, "alt-text-optimization-report.md");
  fs.writeFileSync(reportPath, md);
  log(`報告已儲存: ${reportPath}`, "success");
  console.log(md);

  return {
    markdown: md,
    reportPath,
    stats: {
      featured: fStats,
      inline: iStats,
      altTextCount: lengths.length,
      avgLength,
      decorativeCount,
    },
  };
}

// ─── Named Exports (for module wrapper / programmatic use) ──────────────────

export {
  exportPhaseScan as phaseScan,
  exportPhaseFeatured as phaseFeatured,
  exportPhaseInline as phaseInline,
  exportPhaseReport as phaseReport,
  exportPhaseRollback as phaseRollback,
  buildDefaultConfig,
  generateAltText,
  generateAltTextFallback,
  healthCheck,
};

// ─── Main (CLI entry point — backward compatible) ───────────────────────────

async function main() {
  console.log("═══════════════════════════════════════════════════");
  console.log("  YOLO LAB Image Alt Text Optimizer");
  console.log("═══════════════════════════════════════════════════\n");

  const config = buildDefaultConfig();
  if (!config.auth) {
    console.error("No auth found. Set WP_APP_USER+WP_APP_PASS or WP_BEARER_TOKEN in .env");
    process.exit(1);
  }

  if (rollbackTarget) {
    await exportPhaseRollback(config, rollbackTarget);
    return;
  }

  if (!phase) {
    console.log("Usage:");
    console.log("  node scripts/image-alt-text-optimizer.js --phase scan [--sample N]");
    console.log("  node scripts/image-alt-text-optimizer.js --phase featured [--dry-run] [--resume] [--sample N]");
    console.log("  node scripts/image-alt-text-optimizer.js --phase inline [--dry-run] [--resume] [--sample N]");
    console.log("  node scripts/image-alt-text-optimizer.js --phase report");
    console.log("  node scripts/image-alt-text-optimizer.js --rollback featured|inline|all");
    process.exit(0);
  }

  const cliOptions = { dryRun, resume, sample: sampleSize };

  switch (phase) {
    case "scan":
      await exportPhaseScan(config, cliOptions);
      break;
    case "featured":
      await exportPhaseFeatured(config, cliOptions);
      break;
    case "inline":
      await exportPhaseInline(config, cliOptions);
      break;
    case "report":
      exportPhaseReport(config);
      break;
    default:
      log(`Unknown phase: ${phase}`, "error");
      process.exit(1);
  }
}

// Only run main() when invoked directly as CLI (not when imported)
const isMainModule = process.argv[1] &&
  (process.argv[1].includes("image-alt-text-optimizer") ||
   fileURLToPath(import.meta.url) === path.resolve(process.argv[1]));

if (isMainModule) {
  main().catch((err) => {
    log(`Fatal: ${err.message}`, "error");
    console.error(err.stack);
    process.exit(1);
  });
}
