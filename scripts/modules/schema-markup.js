/**
 * Schema Markup Module Wrapper
 *
 * Combines phase4 generation (JSON-LD schema) and application
 * with backup/rollback support. Importable by the /seo skill.
 *
 * Workflow: scan -> generate -> apply (with backup) -> verify -> report
 */

import path from "path";
import {
  discoverAuth,
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
} from "../lib/seo-shared.js";

import { generateSchemaMarkup } from "../phase4-complete-seo-batch-generator.js";
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

const YOAST_SCHEMA_FIELD = "_yoast_wpseo_schema";

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
 * Scan articles to identify those missing JSON-LD schema markup.
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
      `${baseUrl}/posts?fields=ID,title,date,modified,excerpt,tags,metadata&number=${perPage}&page=${page}`,
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
    const schema = metadata.find(m => m.key === YOAST_SCHEMA_FIELD)?.value || "";

    const hasSchema = schema.trim().length > 0;
    let isValidSchema = false;

    if (hasSchema) {
      try {
        const parsed = JSON.parse(schema);
        isValidSchema = parsed["@context"] === "https://schema.org" && !!parsed["@type"];
      } catch {
        isValidSchema = false;
      }
    }

    if (!hasSchema || !isValidSchema) {
      needsOptimization.push({
        id: post.ID,
        title: post.title,
        date: post.date,
        modified: post.modified,
        tags: post.tags,
        excerpt: post.excerpt,
        hasSchema,
        isValidSchema,
        currentSchema: schema,
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
 * Generate JSON-LD schema markup for a list of articles.
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

  const statePath = path.join(outputDir, "schema-markup-generate-state.json");
  const state = loadState(statePath, { module: "schema-markup", phase: "generate" });
  const processedIds = new Set(state.processed.map(p => p.id));

  const results = [];
  const stats = { success: 0, failed: 0, skipped: 0 };

  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];
    const articleId = article.id || article.ID;

    // Skip already-processed articles (resume support)
    if (processedIds.has(articleId)) {
      stats.skipped++;
      continue;
    }

    // Skip articles that already have valid schema (unless force)
    if (!config.force && article.hasSchema && article.isValidSchema) {
      stats.skipped++;
      state.skipped.push({ id: articleId, reason: "already has valid schema" });
      continue;
    }

    try {
      const result = await generateSchemaMarkup({
        ID: articleId,
        title: article.title,
        tags: article.tags,
        date: article.date,
        modified: article.modified,
        excerpt: article.excerpt,
      });

      results.push({
        id: articleId,
        title: article.title,
        schema: result,
        success: true,
      });

      state.processed.push({ id: articleId, timestamp: new Date().toISOString() });
      stats.success++;

      log(`[SCHEMA] Generated ${i + 1}/${articles.length} (ID: ${articleId})`);
    } catch (err) {
      results.push({
        id: articleId,
        title: article.title,
        success: false,
        error: err.message,
      });
      state.failed.push({ id: articleId, error: err.message });
      stats.failed++;

      log(`[SCHEMA] Failed (ID ${articleId}): ${err.message}`, "error");
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
  const resultsPath = path.join(outputDir, "schema_optimization_results.json");
  saveJSON(resultsPath, {
    task: "schema",
    timestamp: new Date().toISOString(),
    totalArticles: articles.length,
    articles: results,
    stats,
  });

  return { results, stats };
}

// ─── Apply ───────────────────────────────────────────────────────────────

/**
 * Apply generated schema markup to WordPress.
 * Creates backup before writing, supports dry-run.
 *
 * @param {Array} results - Generated schema results (from generate())
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
    `schema-markup-backup-${new Date().toISOString().replace(/[:.]/g, "-")}.json`
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

  const statePath = path.join(outputDir, "schema-markup-apply-state.json");
  const state = loadState(statePath, { module: "schema-markup", phase: "apply" });
  const processedIds = new Set(state.processed.map(p => p.postId));

  let applied = 0;
  let failed = 0;
  const errors = [];

  const successResults = results.filter(r => r.success && r.schema);

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

    // Build and apply metadata (only schema field)
    const metadata = buildMetadataUpdate(postId, { schema: item.schema });
    const result = await updatePostMetadata(postId, mergedConfig, metadata);

    if (result.success) {
      applied++;
      state.processed.push({ postId, timestamp: new Date().toISOString() });
      log(`[SCHEMA] Applied to post ${postId}`, "success");
    } else {
      failed++;
      errors.push({ postId, message: result.error });
      state.failed.push({ postId, error: result.error });
      log(`[SCHEMA] Failed to apply to post ${postId}: ${result.error}`, "error");
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
 * Verify that applied schema markup was actually written.
 *
 * @param {Array} postIds - Post IDs to verify
 * @param {object} expected - Map of postId -> schema object
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
      const actualSchema = metadata.find(m => m.key === YOAST_SCHEMA_FIELD)?.value || "";

      let parsedActual = null;
      try {
        parsedActual = JSON.parse(actualSchema);
      } catch { /* not valid JSON */ }

      const exp = expected[postId];
      // Check that @type matches at minimum
      const typeMatch = parsedActual?.["@type"] === exp?.["@type"];

      if (typeMatch) {
        verified++;
        details.push({ postId, status: "verified" });
      } else {
        mismatched++;
        details.push({
          postId,
          status: "mismatch",
          expected: exp,
          actual: parsedActual,
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
 * Rollback schema markup changes from a backup file.
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
 * Run the complete schema-markup optimization workflow.
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

  log("=== Schema Markup Optimization ===");

  // Step 1: Scan
  log("Phase 1: Scanning for articles needing schema markup...");
  const scanResult = await scan(mergedConfig);
  log(`Found ${scanResult.needsOptimization}/${scanResult.total} articles needing schema`);

  if (scanResult.needsOptimization === 0) {
    return {
      module: "schema-markup",
      status: "complete",
      scan: scanResult,
      generate: { results: [], stats: { success: 0, failed: 0, skipped: 0 } },
      apply: { applied: 0, failed: 0, backupPath: null, errors: [] },
      message: "No articles need schema markup optimization",
    };
  }

  // Step 2: Generate
  log("Phase 2: Generating schema markup...");
  const generateResult = await generate(scanResult.articles, mergedConfig);

  // Step 3: Apply
  log("Phase 3: Applying schema markup to WordPress...");
  const applyResult = await apply(generateResult.results, mergedConfig);

  // Step 4: Verify
  log("Phase 4: Verifying applied schema markup...");
  const appliedIds = generateResult.results
    .filter(r => r.success)
    .map(r => r.id);
  const expectedMap = {};
  generateResult.results.filter(r => r.success).forEach(r => {
    expectedMap[r.id] = r.schema;
  });

  let verifyResult = { verified: 0, mismatched: 0, details: [] };
  if (!mergedConfig.dryRun && appliedIds.length > 0) {
    verifyResult = await verify(appliedIds, expectedMap, mergedConfig);
  }

  // Step 5: Report
  const report = {
    module: "schema-markup",
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

  const reportPath = path.join(outputDir, "schema-markup-report.json");
  saveJSON(reportPath, report);
  log(`Report saved to ${reportPath}`);

  return report;
}
