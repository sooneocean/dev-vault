/**
 * Meta Tags Module Wrapper
 *
 * Combines phase4 generation (meta title + description) and application
 * with backup/rollback support. Importable by the /seo skill.
 *
 * Workflow: scan -> generate -> apply (with backup) -> verify -> report
 */

import path from "path";
import {
  discoverAuth,
  resolveApiBase,
  apiGet,
  apiPost,
  createBackup,
  loadBackup,
  loadState,
  saveState,
  log,
  sleep,
  ensureDir,
  saveJSON,
  loadJSON,
} from "../lib/seo-shared.js";

import { generateMetaOptimization } from "../phase4-complete-seo-batch-generator.js";
import {
  buildMetadataUpdate,
  updatePostMetadata,
  verifyYoastSupport,
  backupPostMetadata,
  rollbackMetadata,
} from "../phase4-apply-seo-to-wordpress.js";

// ─── Constants ───────────────────────────────────────────────────────────

const DEFAULT_CONFIG = {
  blogId: 133512998,
  domain: "yololab.net",
  batchSize: 5,
  delayMs: 2000,
  outputDir: null, // resolved at runtime
};

const YOAST_TITLE_FIELD = "_yoast_wpseo_title";
const YOAST_DESC_FIELD = "_yoast_wpseo_metadesc";

// ─── Helpers ─────────────────────────────────────────────────────────────

function resolveOutputDir(config) {
  return config.outputDir || path.resolve("seo-optimization-output");
}

function getApiBaseUrl(blogId) {
  return `https://public-api.wordpress.com/rest/v1.1/sites/${blogId}`;
}

function getAuthHeaders(config) {
  const auth = discoverAuth({ rootDir: config.rootDir });
  if (auth) return auth.headers;
  throw new Error("No auth credentials found. Set WPCOM_TOKEN or WP_APP_USER+WP_APP_PASS.");
}

// ─── Scan ────────────────────────────────────────────────────────────────

/**
 * Scan articles to identify those missing or with weak meta titles/descriptions.
 *
 * @param {object} config - { blogId, rootDir, sample? }
 * @returns {Promise<{ total: number, needsOptimization: number, articles: Array }>}
 */
export async function scan(config = {}) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  const blogId = mergedConfig.blogId;
  const headers = getAuthHeaders(mergedConfig);
  const baseUrl = getApiBaseUrl(blogId);

  const sample = mergedConfig.sample || 100;
  let allPosts = [];
  let page = 1;

  while (allPosts.length < sample) {
    const perPage = Math.min(100, sample - allPosts.length);
    const data = await apiGet(
      `${baseUrl}/posts?fields=ID,title,excerpt,metadata&number=${perPage}&page=${page}`,
      headers
    );
    if (!data.posts || data.posts.length === 0) break;
    allPosts.push(...data.posts);
    page++;
    await sleep(500);
  }

  const needsOptimization = [];

  for (const post of allPosts) {
    const metadata = post.metadata || [];
    const title = metadata.find(m => m.key === YOAST_TITLE_FIELD)?.value || "";
    const desc = metadata.find(m => m.key === YOAST_DESC_FIELD)?.value || "";

    const hasTitle = title.trim().length > 0;
    const hasDesc = desc.trim().length > 0;

    if (!hasTitle || !hasDesc) {
      needsOptimization.push({
        id: post.ID,
        title: post.title,
        hasMetaTitle: hasTitle,
        hasMetaDesc: hasDesc,
        currentMetaTitle: title,
        currentMetaDesc: desc,
      });
    }
  }

  return {
    total: allPosts.length,
    needsOptimization: needsOptimization.length,
    articles: needsOptimization,
  };
}

// ─── Generate ────────────────────────────────────────────────────────────

/**
 * Generate optimized meta titles and descriptions for a list of articles.
 * Uses Claude API via the phase4 generator.
 *
 * @param {Array} articles - Articles to optimize (from scan or manual list)
 * @param {object} config - { batchSize, delayMs, outputDir }
 * @returns {Promise<{ results: Array, stats: { success: number, failed: number, skipped: number } }>}
 */
export async function generate(articles, config = {}) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  const outputDir = resolveOutputDir(mergedConfig);
  ensureDir(outputDir);

  const statePath = path.join(outputDir, "meta-tags-generate-state.json");
  const state = loadState(statePath, { module: "meta-tags", phase: "generate" });
  const processedIds = new Set(state.processed.map(p => p.id));

  const results = [];
  const stats = { success: 0, failed: 0, skipped: 0 };

  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];

    // Skip already-processed articles (resume support)
    if (processedIds.has(article.id || article.ID)) {
      stats.skipped++;
      continue;
    }

    // Skip articles that already have optimized meta (unless force)
    if (!config.force && article.hasMetaTitle && article.hasMetaDesc) {
      stats.skipped++;
      state.skipped.push({ id: article.id || article.ID, reason: "already optimized" });
      continue;
    }

    try {
      const result = await generateMetaOptimization({
        ID: article.id || article.ID,
        title: article.title,
        tags: article.tags,
        excerpt: article.excerpt,
        date: article.date,
      });

      results.push({
        id: article.id || article.ID,
        title: article.title,
        meta: result,
        success: true,
      });

      state.processed.push({ id: article.id || article.ID, timestamp: new Date().toISOString() });
      stats.success++;

      log(`[META] Generated ${i + 1}/${articles.length} (ID: ${article.id || article.ID})`);
    } catch (err) {
      results.push({
        id: article.id || article.ID,
        title: article.title,
        success: false,
        error: err.message,
      });
      state.failed.push({ id: article.id || article.ID, error: err.message });
      stats.failed++;

      log(`[META] Failed (ID ${article.id || article.ID}): ${err.message}`, "error");
    }

    // Rate limiting
    if (i < articles.length - 1) {
      await sleep(mergedConfig.delayMs);
    }

    // Save state after each batch
    if ((i + 1) % mergedConfig.batchSize === 0) {
      state.stats = stats;
      saveState(statePath, state);
    }
  }

  // Final state save
  state.stats = stats;
  state.endTime = new Date().toISOString();
  saveState(statePath, state);

  // Save results
  const resultsPath = path.join(outputDir, "meta_optimization_results.json");
  saveJSON(resultsPath, {
    task: "meta",
    timestamp: new Date().toISOString(),
    totalArticles: articles.length,
    articles: results,
    stats,
  });

  return { results, stats };
}

// ─── Apply ───────────────────────────────────────────────────────────────

/**
 * Apply generated meta optimizations to WordPress.
 * Creates backup before writing, supports dry-run.
 *
 * @param {Array} results - Generated meta results (from generate())
 * @param {object} config - { blogId, rootDir, dryRun, outputDir }
 * @returns {Promise<{ applied: number, failed: number, backupPath: string, errors: Array }>}
 */
export async function apply(results, config = {}) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  const outputDir = resolveOutputDir(mergedConfig);
  const backupDir = path.join(outputDir, "backups");
  ensureDir(backupDir);

  const backupPath = path.join(
    backupDir,
    `meta-tags-backup-${new Date().toISOString().replace(/[:.]/g, "-")}.json`
  );

  // Verify Yoast support before batch
  const verification = await verifyYoastSupport(mergedConfig);
  if (!verification.ok) {
    return {
      applied: 0,
      failed: 0,
      backupPath: null,
      errors: [{ message: `Yoast fields not supported: ${verification.error}` }],
    };
  }

  const statePath = path.join(outputDir, "meta-tags-apply-state.json");
  const state = loadState(statePath, { module: "meta-tags", phase: "apply" });
  const processedIds = new Set(state.processed.map(p => p.postId));

  let applied = 0;
  let failed = 0;
  const errors = [];

  const successResults = results.filter(r => r.success && r.meta);

  for (let i = 0; i < successResults.length; i++) {
    const item = successResults[i];
    const postId = item.id;

    // Skip already applied (resume)
    if (processedIds.has(postId)) continue;

    // Backup before write
    if (!mergedConfig.dryRun) {
      try {
        await backupPostMetadata(postId, mergedConfig, backupPath);
      } catch (err) {
        log(`Backup failed for post ${postId}: ${err.message}`, "warning");
      }
    }

    // Build and apply metadata
    const metadata = buildMetadataUpdate(postId, { meta: item.meta });
    const result = await updatePostMetadata(postId, mergedConfig, metadata);

    if (result.success) {
      applied++;
      state.processed.push({ postId, timestamp: new Date().toISOString() });
      log(`[META] Applied to post ${postId}`, "success");
    } else {
      failed++;
      errors.push({ postId, message: result.error });
      state.failed.push({ postId, error: result.error });
      log(`[META] Failed to apply to post ${postId}: ${result.error}`, "error");
    }

    // Rate limiting
    if (i < successResults.length - 1) {
      await sleep(mergedConfig.delayMs);
    }

    // Save state periodically
    if ((i + 1) % mergedConfig.batchSize === 0) {
      state.stats = { applied, failed };
      saveState(statePath, state);
    }
  }

  state.stats = { applied, failed };
  state.endTime = new Date().toISOString();
  saveState(statePath, state);

  return { applied, failed, backupPath, errors };
}

// ─── Verify ──────────────────────────────────────────────────────────────

/**
 * Verify that applied meta tags were actually written.
 *
 * @param {Array} postIds - Post IDs to verify
 * @param {object} expected - Map of postId -> { optimizedTitle, metaDescription }
 * @param {object} config - { blogId, rootDir }
 * @returns {Promise<{ verified: number, mismatched: number, details: Array }>}
 */
export async function verify(postIds, expected, config = {}) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  const headers = getAuthHeaders(mergedConfig);
  const baseUrl = getApiBaseUrl(mergedConfig.blogId);

  let verified = 0;
  let mismatched = 0;
  const details = [];

  for (const postId of postIds) {
    try {
      const post = await apiGet(
        `${baseUrl}/posts/${postId}?fields=ID,metadata`,
        headers
      );

      const metadata = post.metadata || [];
      const actualTitle = metadata.find(m => m.key === YOAST_TITLE_FIELD)?.value || "";
      const actualDesc = metadata.find(m => m.key === YOAST_DESC_FIELD)?.value || "";

      const exp = expected[postId];
      const titleMatch = !exp?.optimizedTitle || actualTitle === exp.optimizedTitle;
      const descMatch = !exp?.metaDescription || actualDesc === exp.metaDescription;

      if (titleMatch && descMatch) {
        verified++;
        details.push({ postId, status: "verified" });
      } else {
        mismatched++;
        details.push({
          postId,
          status: "mismatch",
          expected: exp,
          actual: { title: actualTitle, description: actualDesc },
        });
      }
    } catch (err) {
      mismatched++;
      details.push({ postId, status: "error", error: err.message });
    }

    await sleep(500);
  }

  return { verified, mismatched, details };
}

// ─── Rollback ────────────────────────────────────────────────────────────

/**
 * Rollback meta tag changes from a backup file.
 *
 * @param {string} backupPath - Path to backup JSON
 * @param {object} config - { blogId, rootDir }
 * @param {object} [options] - { postIds?: number[] }
 * @returns {Promise<{ restored: number, failed: number, errors: Array }>}
 */
export async function rollback(backupPath, config = {}, options = {}) {
  return rollbackMetadata(backupPath, config, options);
}

// ─── Full Workflow ───────────────────────────────────────────────────────

/**
 * Run the complete meta-tags optimization workflow.
 * scan -> generate -> apply (with backup) -> verify -> report
 *
 * @param {object} config - Full config object
 * @param {object} [options] - { dryRun, sample, force }
 * @returns {Promise<object>} Full workflow report
 */
export async function run(config = {}, options = {}) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config, ...options };
  const outputDir = resolveOutputDir(mergedConfig);
  ensureDir(outputDir);

  log("=== Meta Tags Optimization ===");

  // Step 1: Scan
  log("Phase 1: Scanning for articles needing meta optimization...");
  const scanResult = await scan(mergedConfig);
  log(`Found ${scanResult.needsOptimization}/${scanResult.total} articles needing optimization`);

  if (scanResult.needsOptimization === 0) {
    return {
      module: "meta-tags",
      status: "complete",
      scan: scanResult,
      generate: { results: [], stats: { success: 0, failed: 0, skipped: 0 } },
      apply: { applied: 0, failed: 0, backupPath: null, errors: [] },
      message: "No articles need meta tag optimization",
    };
  }

  // Step 2: Generate
  log("Phase 2: Generating optimized meta tags...");
  const generateResult = await generate(scanResult.articles, mergedConfig);

  // Step 3: Apply
  log("Phase 3: Applying meta tags to WordPress...");
  const applyResult = await apply(generateResult.results, mergedConfig);

  // Step 4: Verify
  log("Phase 4: Verifying applied meta tags...");
  const appliedIds = generateResult.results
    .filter(r => r.success)
    .map(r => r.id);
  const expectedMap = {};
  generateResult.results.filter(r => r.success).forEach(r => {
    expectedMap[r.id] = r.meta;
  });

  let verifyResult = { verified: 0, mismatched: 0, details: [] };
  if (!mergedConfig.dryRun && appliedIds.length > 0) {
    verifyResult = await verify(appliedIds, expectedMap, mergedConfig);
  }

  // Step 5: Report
  const report = {
    module: "meta-tags",
    timestamp: new Date().toISOString(),
    status: "complete",
    scan: {
      total: scanResult.total,
      needsOptimization: scanResult.needsOptimization,
    },
    generate: generateResult.stats,
    apply: {
      applied: applyResult.applied,
      failed: applyResult.failed,
      backupPath: applyResult.backupPath,
    },
    verify: {
      verified: verifyResult.verified,
      mismatched: verifyResult.mismatched,
    },
  };

  const reportPath = path.join(outputDir, "meta-tags-report.json");
  saveJSON(reportPath, report);
  log(`Report saved to ${reportPath}`);

  return report;
}
