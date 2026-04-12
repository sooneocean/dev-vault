/**
 * Internal Links Module — Thin Adapter
 *
 * Wraps internal-linker-v2.js for the SEO Orchestrator skill.
 * Provides a config-driven interface with backup/rollback.
 *
 * Usage:
 *   import { run, phases } from './internal-links.js';
 *   const result = await run('propose', { siteId: 133512998, domain: 'yololab.net', ... });
 */

import {
  fetchMap,
  generateProposals,
  injectLinks,
  fixBrokenLinks,
  rollbackLinks,
  RELATED_MARKER,
} from "../internal-linker-v2.js";

import { loadSiteConfig } from "../lib/seo-shared.js";

// ─── Available phases ───────────────────────────────────────────────────────

export const phases = ["fetch-map", "propose", "inject", "fix-broken", "rollback"];

// ─── Config Builder ─────────────────────────────────────────────────────────

/**
 * Build module config from site name or explicit config.
 *
 * @param {string|object} siteOrConfig - Site name (e.g., "yololab") or config object
 * @param {string} [rootDir] - Project root directory
 * @returns {object} Merged config for internal-linker-v2 functions
 */
export function buildConfig(siteOrConfig, rootDir) {
  if (typeof siteOrConfig === "object" && siteOrConfig !== null) {
    return siteOrConfig;
  }

  const siteConfig = loadSiteConfig(siteOrConfig, rootDir);
  if (!siteConfig) {
    throw new Error(`Site "${siteOrConfig}" not found in site-optimizer-config.json`);
  }

  return {
    siteId: siteConfig.siteId,
    domain: siteConfig.domain,
    rootDir,
  };
}

// ─── Run Phase ──────────────────────────────────────────────────────────────

/**
 * Run an internal-links phase with config.
 *
 * @param {string} phase - One of: fetch-map, propose, inject, fix-broken, rollback
 * @param {object} config - Config object (siteId, domain, dataDir, outputDir, rootDir, rateLimit)
 * @param {object} [options] - Phase-specific options (e.g., { dryRun: true } for inject)
 * @returns {Promise<object>} Phase result
 */
export async function run(phase, config, options = {}) {
  switch (phase) {
    case "fetch-map":
      return await fetchMap(config);
    case "propose":
      return generateProposals(config);
    case "inject":
      return await injectLinks(config, options);
    case "fix-broken":
      return await fixBrokenLinks(config);
    case "rollback":
      return await rollbackLinks(config);
    default:
      throw new Error(`Unknown phase: ${phase}. Available: ${phases.join(", ")}`);
  }
}

// ─── Re-exports for direct access ───────────────────────────────────────────

export {
  fetchMap,
  generateProposals,
  injectLinks,
  fixBrokenLinks,
  rollbackLinks,
  RELATED_MARKER,
};
