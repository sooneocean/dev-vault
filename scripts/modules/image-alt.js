/**
 * Image ALT Module Wrapper
 *
 * Thin adapter around image-alt-text-optimizer.js for the SEO Orchestrator skill.
 * Loads config, calls the right phase function, returns structured result.
 */

import path from "path";
import { fileURLToPath } from "url";
import {
  discoverAuth,
  resolveApiBase,
  loadSiteConfig,
  DEFAULT_RATE_LIMIT,
} from "../lib/seo-shared.js";
import {
  phaseScan,
  phaseFeatured,
  phaseInline,
  phaseReport,
  phaseRollback,
  buildDefaultConfig,
} from "../image-alt-text-optimizer.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.join(__dirname, "../..");

// ─── Config Builder ─────────────────────────────────────────────────────────

/**
 * Build a config object for image-alt operations.
 *
 * @param {object} [opts] - Override options
 * @param {string} [opts.site] - Site name from site-optimizer-config.json (default: "yololab")
 * @param {string} [opts.outputDir] - Custom output directory
 * @param {object} [opts.rateLimit] - Custom rate limit settings
 * @param {string} [opts.rootDir] - Project root directory
 * @returns {object} Config object ready for phase functions
 */
export function buildConfig(opts = {}) {
  const rootDir = opts.rootDir || PROJECT_ROOT;
  const siteName = opts.site || "yololab";

  // Try loading from site-optimizer-config.json first
  const siteConfig = loadSiteConfig(siteName, rootDir);

  let siteId, domain;
  if (siteConfig) {
    siteId = siteConfig.siteId;
    domain = siteConfig.domain;
  } else {
    // Fallback to hardcoded defaults (yololab)
    const defaults = buildDefaultConfig();
    siteId = defaults.siteId;
    domain = defaults.domain;
  }

  const auth = discoverAuth({ rootDir });
  if (!auth) {
    return {
      siteId,
      domain,
      apiBase: null,
      apiV1: null,
      auth: null,
      outputDir: opts.outputDir || path.join(rootDir, "seo-optimization-output"),
      rateLimit: opts.rateLimit || { ...DEFAULT_RATE_LIMIT },
      rootDir,
      error: "No auth credentials found",
    };
  }

  const apiBase = resolveApiBase({ siteId, domain }, auth);
  const apiV1 = `https://public-api.wordpress.com/rest/v1.1/sites/${siteId}`;

  return {
    siteId,
    domain,
    apiBase,
    apiV1,
    auth,
    outputDir: opts.outputDir || path.join(rootDir, "seo-optimization-output"),
    rateLimit: opts.rateLimit || { ...DEFAULT_RATE_LIMIT },
    visionModel: "claude-haiku-4-5-20251001",
    rootDir,
  };
}

// ─── Module Entry Points ────────────────────────────────────────────────────

/**
 * Run a scan audit of image alt text across the site.
 *
 * @param {object} [opts] - { site, sample, outputDir, skipLock, skipHealthCheck }
 * @returns {Promise<{ ok: boolean, phase: string, report?: object, error?: string }>}
 */
export async function scan(opts = {}) {
  try {
    const config = buildConfig(opts);
    if (!config.auth) {
      return { ok: false, phase: "scan", error: config.error || "No auth" };
    }
    const report = await phaseScan(config, {
      sample: opts.sample || 0,
      skipLock: opts.skipLock,
      skipHealthCheck: opts.skipHealthCheck,
    });
    return { ok: true, phase: "scan", report };
  } catch (err) {
    return { ok: false, phase: "scan", error: err.message };
  }
}

/**
 * Update featured media alt text using Claude Vision.
 *
 * @param {object} [opts] - { site, sample, dryRun, resume, outputDir, skipVerification }
 * @returns {Promise<{ ok: boolean, phase: string, state?: object, error?: string }>}
 */
export async function featured(opts = {}) {
  try {
    const config = buildConfig(opts);
    if (!config.auth) {
      return { ok: false, phase: "featured", error: config.error || "No auth" };
    }
    const state = await phaseFeatured(config, {
      dryRun: opts.dryRun,
      resume: opts.resume,
      sample: opts.sample || 0,
      skipVerification: opts.skipVerification,
    });
    return { ok: true, phase: "featured", state };
  } catch (err) {
    return { ok: false, phase: "featured", error: err.message };
  }
}

/**
 * Update inline image alt text in post content.
 *
 * @param {object} [opts] - { site, sample, dryRun, resume, outputDir, skipVerification }
 * @returns {Promise<{ ok: boolean, phase: string, state?: object, error?: string }>}
 */
export async function inline(opts = {}) {
  try {
    const config = buildConfig(opts);
    if (!config.auth) {
      return { ok: false, phase: "inline", error: config.error || "No auth" };
    }
    const state = await phaseInline(config, {
      dryRun: opts.dryRun,
      resume: opts.resume,
      sample: opts.sample || 0,
      skipVerification: opts.skipVerification,
    });
    return { ok: true, phase: "inline", state };
  } catch (err) {
    return { ok: false, phase: "inline", error: err.message };
  }
}

/**
 * Generate quality verification report.
 *
 * @param {object} [opts] - { site, outputDir }
 * @returns {{ ok: boolean, phase: string, report?: object, error?: string }}
 */
export function report(opts = {}) {
  try {
    const config = buildConfig(opts);
    const result = phaseReport(config);
    return { ok: true, phase: "report", report: result };
  } catch (err) {
    return { ok: false, phase: "report", error: err.message };
  }
}

/**
 * Rollback alt text changes from backup.
 *
 * @param {string} target - "featured" | "inline" | "all"
 * @param {object} [opts] - { site, outputDir, skipVerification }
 * @returns {Promise<{ ok: boolean, phase: string, results?: object, error?: string }>}
 */
export async function rollback(target, opts = {}) {
  try {
    const config = buildConfig(opts);
    if (!config.auth) {
      return { ok: false, phase: "rollback", error: config.error || "No auth" };
    }
    const result = await phaseRollback(config, target, {
      skipVerification: opts.skipVerification,
    });
    return { ok: true, phase: "rollback", results: result.results };
  } catch (err) {
    return { ok: false, phase: "rollback", error: err.message };
  }
}

// Re-export for advanced usage
export { buildDefaultConfig } from "../image-alt-text-optimizer.js";
