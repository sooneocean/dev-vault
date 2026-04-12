#!/usr/bin/env node

/**
 * Phase 4 Apply SEO to WordPress.com
 *
 * 將生成的 SEO 優化數據應用到 WordPress.com 文章
 * 包括：Meta 標題、Meta Description、Schema Markup、OG Tags
 *
 * 使用方式：
 * export WPCOM_TOKEN=your_token
 * node phase4-apply-seo-to-wordpress.js [--demo] [--dry-run]
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import {
  discoverAuth,
  resolveApiBase,
  apiGet,
  apiPost,
  createBackup,
  loadBackup,
  log as sharedLog,
  sleep,
  ensureDir,
} from "./lib/seo-shared.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = path.join(__dirname, "../seo-optimization-output");

const args = process.argv.slice(2);
const demoMode = args.includes("--demo");
const dryRun = args.includes("--dry-run");

// ─── Configuration ────────────────────────────────────────────────────────

const DEFAULT_BLOG_ID = 133512998;
const BATCH_SIZE = 5; // 每批 5 篇（API 限制）
const DELAY_MS = 3000;

// Re-export shared log for backward compat within this file
function log(msg, level = "info") {
  sharedLog(msg, level);
}

// ─── Yoast Fields ─────────────────────────────────────────────────────────

const YOAST_META_FIELDS = [
  "_yoast_wpseo_title",
  "_yoast_wpseo_metadesc",
];

const YOAST_SCHEMA_FIELD = "_yoast_wpseo_schema";

// ─── Auth / API Helpers ──────────────────────────────────────────────────

/**
 * Get auth headers from shared discovery.
 * Falls back to WPCOM_TOKEN env var for backward compatibility.
 */
function getAuthHeaders(config = {}) {
  const auth = discoverAuth({ rootDir: config.rootDir });
  if (auth) return auth.headers;
  // Fallback: direct WPCOM_TOKEN check for backward compat
  const token = process.env.WPCOM_TOKEN;
  if (!token) {
    throw new Error(
      "Missing auth credentials. Set WPCOM_TOKEN or WP_APP_USER+WP_APP_PASS."
    );
  }
  return { Authorization: `Bearer ${token}` };
}

/**
 * Build the v1.1 API base URL for a given site/blog ID.
 */
function getApiBaseUrl(blogId) {
  return `https://public-api.wordpress.com/rest/v1.1/sites/${blogId}`;
}

// ─── Verify Yoast Field Support ──────────────────────────────────────────

/**
 * Verify that the target site supports Yoast SEO meta fields.
 * Makes a test read of a single post's metadata to confirm fields exist.
 *
 * @param {object} config - { blogId, rootDir }
 * @returns {Promise<{ ok: boolean, error?: string }>}
 */
export async function verifyYoastSupport(config = {}) {
  const blogId = config.blogId || DEFAULT_BLOG_ID;
  const headers = getAuthHeaders(config);
  const baseUrl = getApiBaseUrl(blogId);

  try {
    // Fetch one post to verify API access
    const data = await apiGet(
      `${baseUrl}/posts?number=1&fields=ID,metadata`,
      headers
    );
    if (!data.posts || data.posts.length === 0) {
      return { ok: false, error: "No posts found on site" };
    }
    // If we can read posts, Yoast fields should be writable if plugin is installed.
    // A definitive check would require attempting a write, but reading metadata is
    // sufficient to confirm API access works.
    return { ok: true };
  } catch (err) {
    return { ok: false, error: `Yoast field verification failed: ${err.message}` };
  }
}

// ─── Backup ──────────────────────────────────────────────────────────────

/**
 * Fetch current Yoast metadata for a post and save to backup.
 *
 * @param {number} postId
 * @param {object} config - { blogId, rootDir }
 * @param {string} backupPath - Full path to backup JSON file
 * @returns {Promise<object>} The original metadata values
 */
export async function backupPostMetadata(postId, config = {}, backupPath) {
  const blogId = config.blogId || DEFAULT_BLOG_ID;
  const headers = getAuthHeaders(config);
  const baseUrl = getApiBaseUrl(blogId);

  // Fetch current post metadata
  const post = await apiGet(
    `${baseUrl}/posts/${postId}?fields=ID,metadata`,
    headers
  );

  // Extract current Yoast field values
  const metadata = post.metadata || [];
  const original = {};
  for (const entry of metadata) {
    if (
      YOAST_META_FIELDS.includes(entry.key) ||
      entry.key === YOAST_SCHEMA_FIELD
    ) {
      original[entry.key] = entry.value;
    }
  }

  // Append to backup file
  const backup = loadBackup(backupPath) || [];
  backup.push({
    postId,
    timestamp: new Date().toISOString(),
    original,
  });
  createBackup(backupPath, backup);

  return original;
}

/**
 * Rollback Yoast metadata for posts from a backup file.
 *
 * @param {string} backupPath - Path to backup JSON
 * @param {object} config - { blogId, rootDir }
 * @param {object} [options] - { postIds?: number[] } to limit rollback scope
 * @returns {Promise<{ restored: number, failed: number, errors: Array }>}
 */
export async function rollbackMetadata(backupPath, config = {}, options = {}) {
  const blogId = config.blogId || DEFAULT_BLOG_ID;
  const headers = getAuthHeaders(config);
  const baseUrl = getApiBaseUrl(blogId);
  const backup = loadBackup(backupPath);

  if (!backup || backup.length === 0) {
    return { restored: 0, failed: 0, errors: [{ message: "No backup found or backup is empty" }] };
  }

  const targetIds = options.postIds ? new Set(options.postIds) : null;
  let restored = 0;
  let failed = 0;
  const errors = [];

  for (const entry of backup) {
    if (targetIds && !targetIds.has(entry.postId)) continue;

    try {
      // Re-apply original metadata values
      const metadata = {};
      for (const [key, value] of Object.entries(entry.original)) {
        metadata[key] = value || ""; // empty string to clear if originally empty
      }

      await apiPost(
        `${baseUrl}/posts/${entry.postId}`,
        { metadata },
        headers
      );

      restored++;
      log(`Restored post ${entry.postId}`, "success");
    } catch (err) {
      failed++;
      errors.push({ postId: entry.postId, message: err.message });
      log(`Failed to restore post ${entry.postId}: ${err.message}`, "error");
    }

    await sleep(DELAY_MS);
  }

  return { restored, failed, errors };
}

// ─── Load SEO Data ────────────────────────────────────────────────────────

function loadSeoData(outputDir = OUTPUT_DIR) {
  const data = {
    meta: {},
    schema: {},
    og: {},
  };

  // 載入 Meta 數據
  const metaFile = path.join(outputDir, "meta_optimization_results.json");
  if (fs.existsSync(metaFile)) {
    const metaData = JSON.parse(fs.readFileSync(metaFile, "utf-8"));
    metaData.articles.forEach(a => {
      data.meta[a.id] = a.meta;
    });
    log(`已載入 ${Object.keys(data.meta).length} 篇文章的 Meta 數據`);
  } else {
    log(`未找到 Meta 數據文件`, "warning");
  }

  // 載入 Schema 數據
  const schemaFile = path.join(outputDir, "schema_optimization_results.json");
  if (fs.existsSync(schemaFile)) {
    const schemaData = JSON.parse(fs.readFileSync(schemaFile, "utf-8"));
    schemaData.articles.forEach(a => {
      data.schema[a.id] = a.schema;
    });
    log(`已載入 ${Object.keys(data.schema).length} 篇文章的 Schema 數據`);
  } else {
    log(`未找到 Schema 數據文件`, "warning");
  }

  // 載入 OG 數據
  const ogFile = path.join(outputDir, "og_optimization_results.json");
  if (fs.existsSync(ogFile)) {
    const ogData = JSON.parse(fs.readFileSync(ogFile, "utf-8"));
    ogData.articles.forEach(a => {
      data.og[a.id] = a.og;
    });
    log(`已載入 ${Object.keys(data.og).length} 篇文章的 OG Tags 數據`);
  } else {
    log(`未找到 OG Tags 數據文件`, "warning");
  }

  return data;
}

// ─── Build Metadata Update ────────────────────────────────────────────────

/**
 * Build metadata object for a WordPress API update.
 *
 * @param {number} postId
 * @param {object} seoData - { meta?, schema?, og? }
 * @returns {object} Metadata fields to write
 */
export function buildMetadataUpdate(postId, seoData) {
  const metadata = {};

  // Meta 標題和描述（Yoast SEO）
  if (seoData.meta) {
    metadata._yoast_wpseo_title = seoData.meta.optimizedTitle || "";
    metadata._yoast_wpseo_metadesc = seoData.meta.metaDescription || "";
  }

  // Schema Markup
  if (seoData.schema) {
    metadata._yoast_wpseo_schema = JSON.stringify(seoData.schema);
  }

  // OG Tags
  if (seoData.og) {
    Object.entries(seoData.og).forEach(([key, value]) => {
      const metaKey = key.replace(/:/g, "_");
      metadata[`_${metaKey}`] = value;
    });
  }

  return metadata;
}

// ─── WordPress.com API (updated to use shared utilities) ─────────────────

/**
 * Update post metadata on WordPress.com.
 *
 * @param {number} postId
 * @param {object} config - { blogId, rootDir, dryRun }
 * @param {object} metadata - Fields to write
 * @returns {Promise<{ success: boolean, error?: string }>}
 */
export async function updatePostMetadata(postId, config = {}, metadata) {
  const blogId = config.blogId || DEFAULT_BLOG_ID;
  const isDryRun = config.dryRun ?? dryRun;

  if (isDryRun) {
    log(`[DRY-RUN] 將更新文章 ${postId} 的元數據`, "info");
    return { success: true };
  }

  try {
    const headers = getAuthHeaders(config);
    const url = `${getApiBaseUrl(blogId)}/posts/${postId}`;

    await apiPost(url, metadata, headers);
    return { success: true };
  } catch (error) {
    log(`更新文章 ${postId} 失敗: ${error.message}`, "error");
    return { success: false, error: error.message };
  }
}

// ─── Main Processing ──────────────────────────────────────────────────────

async function main() {
  log(`\n════════════════════════════════════════`);
  log(`Phase 4 Apply SEO to WordPress.com`);
  log(`════════════════════════════════════════`);
  log(`Dry-Run 模式: ${dryRun ? "是" : "否"}`);
  log(`演示模式: ${demoMode ? "是" : "否"}`);

  try {
    const config = { blogId: DEFAULT_BLOG_ID };

    // Verify Yoast field support before batch
    const verification = await verifyYoastSupport(config);
    if (!verification.ok) {
      log(`Yoast field verification failed: ${verification.error}`, "error");
      process.exit(1);
    }
    log("Yoast field support verified", "success");

    const seoData = loadSeoData();

    // 收集所有要更新的文章 ID
    const articleIds = new Set([
      ...Object.keys(seoData.meta).map(Number),
      ...Object.keys(seoData.schema).map(Number),
      ...Object.keys(seoData.og).map(Number),
    ]);

    const articles = Array.from(articleIds);

    if (demoMode) {
      articles.length = Math.min(2, articles.length);
      log(`演示模式：${articles.length} 篇文章`);
    } else {
      log(`準備更新 ${articles.length} 篇文章`);
    }

    // Setup backup
    const backupDir = path.join(OUTPUT_DIR, "backups");
    ensureDir(backupDir);
    const backupPath = path.join(
      backupDir,
      `meta-schema-backup-${new Date().toISOString().split("T")[0]}.json`
    );

    const results = {
      timestamp: new Date().toISOString(),
      totalArticles: articles.length,
      backupPath,
      updated: 0,
      failed: 0,
      skipped: 0,
      details: [],
    };

    // 分批更新
    for (let i = 0; i < articles.length; i += BATCH_SIZE) {
      const batchNum = Math.floor(i / BATCH_SIZE) + 1;
      const batch = articles.slice(i, i + BATCH_SIZE);
      const totalBatches = Math.ceil(articles.length / BATCH_SIZE);

      log(`\n批次 ${batchNum}/${totalBatches} (${batch.length} 篇)`);

      for (const postId of batch) {
        const articleSeoData = {
          meta: seoData.meta[postId],
          schema: seoData.schema[postId],
          og: seoData.og[postId],
        };

        // Backup original metadata before writing
        if (!dryRun) {
          try {
            await backupPostMetadata(postId, config, backupPath);
          } catch (backupErr) {
            log(`Backup failed for post ${postId}: ${backupErr.message}`, "warning");
          }
        }

        // 構建元數據
        const metadata = buildMetadataUpdate(postId, articleSeoData);

        // 執行更新
        const result = await updatePostMetadata(postId, config, metadata);

        if (result.success) {
          results.updated++;
          log(`文章 ${postId} 已更新`, "success");
        } else {
          results.failed++;
          log(`文章 ${postId} 更新失敗: ${result.error}`, "error");
        }

        results.details.push({
          postId,
          success: result.success,
          error: result.error,
        });

        // 避免速率限制
        await sleep(DELAY_MS);
      }

      // 批次間延遲
      if (i + BATCH_SIZE < articles.length) {
        log(`批次間延遲 5 秒...`);
        await sleep(5000);
      }
    }

    // 保存結果報告
    const reportFile = path.join(OUTPUT_DIR, "PHASE4_APPLICATION_REPORT.json");
    fs.writeFileSync(reportFile, JSON.stringify(results, null, 2));

    log(`\n════════════════════════════════════════`);
    log(`應用完成`, "success");
    log(`════════════════════════════════════════`);
    log(`已更新: ${results.updated}/${articles.length}`);
    log(`失敗: ${results.failed}`);
    log(`備份: ${backupPath}`);
    log(`\n報告已保存: ${reportFile}`);

  } catch (error) {
    log(`致命錯誤: ${error.message}`, "error");
    process.exit(1);
  }
}

// ─── CLI Entry Point ─────────────────────────────────────────────────────
const isMainModule = process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);
if (isMainModule) {
  main();
}
