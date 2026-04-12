/**
 * SEO Orchestrator — State Management
 *
 * Handles cross-session resume, audit cache, and orchestrator state persistence.
 * Used by the /seo skill to detect interrupted batches and offer resume.
 */

import fs from "fs";
import path from "path";
import { loadJSON, saveJSON, ensureDir, log } from "./seo-shared.js";

const OUTPUT_DIR = "seo-optimization-output";
const STATE_FILE = "seo-orchestrator-state.json";
const AUDIT_CACHE_FILE = "audit-cache.json";
const LOCK_FILE = "seo-orchestrator.lock";

// ─── Orchestrator State ─────────────────────────────────────────────────────

/**
 * Load orchestrator state. Returns null if no active session.
 *
 * @param {string} [rootDir] - Project root directory
 * @returns {object|null} State object or null
 */
export function loadOrchestratorState(rootDir = process.cwd()) {
  const statePath = path.join(rootDir, OUTPUT_DIR, STATE_FILE);
  return loadJSON(statePath);
}

/**
 * Save orchestrator state for cross-session resume.
 *
 * @param {object} state - State to persist
 * @param {string} [rootDir] - Project root directory
 */
export function saveOrchestratorState(state, rootDir = process.cwd()) {
  const statePath = path.join(rootDir, OUTPUT_DIR, STATE_FILE);
  saveJSON(statePath, {
    ...state,
    lastUpdated: new Date().toISOString(),
  });
}

/**
 * Clear orchestrator state (after completion or abandon).
 *
 * @param {string} [rootDir] - Project root directory
 */
export function clearOrchestratorState(rootDir = process.cwd()) {
  const statePath = path.join(rootDir, OUTPUT_DIR, STATE_FILE);
  if (fs.existsSync(statePath)) {
    fs.unlinkSync(statePath);
  }
}

/**
 * Check if an orchestrator state represents an interrupted session.
 *
 * @param {object|null} state - Loaded state
 * @param {number} [staleHours=24] - Hours after which state is considered abandoned
 * @returns {{ interrupted: boolean, stale: boolean, module?: string, progress?: string }}
 */
export function checkSessionStatus(state, staleHours = 24) {
  if (!state) return { interrupted: false, stale: false };

  const age = Date.now() - new Date(state.lastUpdated || state.startTime).getTime();
  const staleMs = staleHours * 3600 * 1000;

  if (age > staleMs) {
    return {
      interrupted: true,
      stale: true,
      module: state.activeModule,
      progress: `${state.articlesProcessed || 0}/${(state.articlesProcessed || 0) + (state.articlesRemaining || 0)}`,
    };
  }

  if (state.activeModule && state.articlesRemaining > 0) {
    return {
      interrupted: true,
      stale: false,
      module: state.activeModule,
      progress: `${state.articlesProcessed || 0}/${(state.articlesProcessed || 0) + (state.articlesRemaining || 0)}`,
    };
  }

  return { interrupted: false, stale: false };
}

// ─── Audit Cache ────────────────────────────────────────────────────────────

/**
 * Load cached audit results.
 *
 * @param {string} [rootDir] - Project root directory
 * @returns {object|null} Cached audit or null
 */
export function loadAuditCache(rootDir = process.cwd()) {
  const cachePath = path.join(rootDir, OUTPUT_DIR, AUDIT_CACHE_FILE);
  return loadJSON(cachePath);
}

/**
 * Save audit results to cache.
 *
 * @param {object} auditData - Audit results by module
 * @param {string} [rootDir] - Project root directory
 */
export function saveAuditCache(auditData, rootDir = process.cwd()) {
  const cachePath = path.join(rootDir, OUTPUT_DIR, AUDIT_CACHE_FILE);
  saveJSON(cachePath, {
    timestamp: new Date().toISOString(),
    modules: auditData,
  });
}

/**
 * Check if cached audit is fresh enough to use.
 *
 * @param {object|null} cache - Loaded cache
 * @param {number} [maxAgeDays=7] - Maximum age in days
 * @returns {boolean}
 */
export function isAuditCacheFresh(cache, maxAgeDays = 7) {
  if (!cache?.timestamp) return false;
  const age = Date.now() - new Date(cache.timestamp).getTime();
  return age < maxAgeDays * 24 * 3600 * 1000;
}

// ─── Path Helpers ───────────────────────────────────────────────────────────

/**
 * Get standard paths for the orchestrator.
 *
 * @param {string} [rootDir] - Project root directory
 * @returns {object} Paths object
 */
export function getOrchestratorPaths(rootDir = process.cwd()) {
  const outputDir = path.join(rootDir, OUTPUT_DIR);
  return {
    outputDir,
    statePath: path.join(outputDir, STATE_FILE),
    auditCachePath: path.join(outputDir, AUDIT_CACHE_FILE),
    lockPath: path.join(outputDir, LOCK_FILE),
    backupsDir: path.join(outputDir, "backups"),
  };
}
