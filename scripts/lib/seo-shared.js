/**
 * SEO Orchestrator — Shared Utilities
 *
 * Extracted from image-alt-text-optimizer.js (production-proven patterns).
 * Provides: auth discovery, API fetch with retry, backup, state management,
 * file locking, and common helpers.
 *
 * All functions accept config/options parameters — no global state.
 */

import fs from "fs";
import path from "path";
import { createReadStream, createWriteStream } from "fs";
import readline from "readline";

// ─── Auth ───────────────────────────────────────────────────────────────────

/**
 * Discover auth credentials from environment, .env file, or .mcp.json.
 * Priority: WPCOM_TOKEN → WP_BEARER_TOKEN → WP_APP_USER+WP_APP_PASS → .mcp.json
 *
 * @param {object} opts
 * @param {string} [opts.rootDir] - Project root for .env/.mcp.json lookup
 * @returns {{ method: string, headers: object, apiBase: string }}
 */
export function discoverAuth(opts = {}) {
  const rootDir = opts.rootDir || process.cwd();

  // 1. Application Password from env vars
  const user = process.env.WP_APP_USER || process.env.WP_USERNAME;
  const pass = process.env.WP_APP_PASS || process.env.WP_APP_PASSWORD;
  if (user && pass) {
    const encoded = Buffer.from(`${user}:${pass}`).toString("base64");
    return {
      method: "basic",
      headers: { Authorization: `Basic ${encoded}` },
      apiBase: "direct", // caller resolves to wp-json URL
    };
  }

  // 2. Application Password from .env file
  const envPath = path.join(rootDir, ".env");
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, "utf-8");
    const userMatch = envContent.match(/(?:WP_APP_USER|WP_USERNAME)=(.+)/);
    const passMatch = envContent.match(/(?:WP_APP_PASS|WP_APP_PASSWORD)=(.+)/);
    if (userMatch && passMatch) {
      const encoded = Buffer.from(
        `${userMatch[1].trim()}:${passMatch[1].trim()}`
      ).toString("base64");
      return {
        method: "basic",
        headers: { Authorization: `Basic ${encoded}` },
        apiBase: "direct",
      };
    }
  }

  // 3. Bearer token from env vars
  const token = process.env.WPCOM_TOKEN || process.env.WP_BEARER_TOKEN;
  if (token) {
    return {
      method: "bearer",
      headers: { Authorization: `Bearer ${token}` },
      apiBase: "wpcom-proxy",
    };
  }

  // 4. Bearer token from .env file
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, "utf-8");
    const match = envContent.match(/(?:WPCOM_TOKEN|WP_BEARER_TOKEN)=(.+)/);
    if (match) {
      return {
        method: "bearer",
        headers: { Authorization: `Bearer ${match[1].trim()}` },
        apiBase: "wpcom-proxy",
      };
    }
  }

  // 5. Token from .mcp.json
  const mcpPath = path.join(rootDir, ".mcp.json");
  if (fs.existsSync(mcpPath)) {
    try {
      const mcp = JSON.parse(fs.readFileSync(mcpPath, "utf-8"));
      const auth = mcp.mcpServers?.["wpcom-mcp"]?.headers?.Authorization;
      if (auth) {
        return {
          method: "bearer",
          headers: { Authorization: auth.startsWith("Bearer ") ? auth : `Bearer ${auth}` },
          apiBase: "wpcom-proxy",
        };
      }
    } catch { /* ignore parse errors */ }
  }

  return null;
}

/**
 * Resolve the API base URL for a site config + auth result.
 *
 * @param {object} siteConfig - { siteId, domain }
 * @param {object} auth - Result from discoverAuth()
 * @param {"wp/v2"|"v1.1"} [apiVersion="wp/v2"]
 * @returns {string} Full API base URL
 */
export function resolveApiBase(siteConfig, auth, apiVersion = "wp/v2") {
  if (apiVersion === "v1.1") {
    return `https://public-api.wordpress.com/rest/v1.1/sites/${siteConfig.siteId}`;
  }
  if (auth.apiBase === "direct") {
    return `https://${siteConfig.domain}/wp-json/wp/v2`;
  }
  return `https://public-api.wordpress.com/wp/v2/sites/${siteConfig.siteId}`;
}

/**
 * Verify auth credentials work by making a test API call.
 *
 * @param {object} siteConfig - { siteId, domain }
 * @param {object} [opts] - { rootDir }
 * @returns {Promise<{ ok: boolean, method: string, apiBase: string, error?: string }>}
 */
export async function verifyAuth(siteConfig, opts = {}) {
  const auth = discoverAuth(opts);
  if (!auth) {
    return { ok: false, method: "none", apiBase: "", error: "No credentials found. Set WPCOM_TOKEN or WP_APP_USER+WP_APP_PASS." };
  }
  const base = resolveApiBase(siteConfig, auth);
  try {
    const res = await fetch(`${base}/posts?per_page=1&_fields=id`, { headers: auth.headers });
    if (!res.ok) {
      return { ok: false, method: auth.method, apiBase: base, error: `Auth failed: HTTP ${res.status}` };
    }
    return { ok: true, method: auth.method, apiBase: base };
  } catch (err) {
    return { ok: false, method: auth.method, apiBase: base, error: err.message };
  }
}

// ─── API Helpers ────────────────────────────────────────────────────────────

const DEFAULT_RATE_LIMIT = {
  batchSize: 5,
  delayMs: 2000,
  retries: 3,
  backoffMs: 3000,
};

/**
 * GET request with retry and rate-limit handling.
 *
 * @param {string} url - Full URL to fetch
 * @param {object} headers - Auth headers
 * @param {object} [rateLimit] - { retries, backoffMs }
 * @returns {Promise<any>} Parsed JSON response
 */
export async function apiGet(url, headers, rateLimit = DEFAULT_RATE_LIMIT) {
  for (let attempt = 1; attempt <= rateLimit.retries; attempt++) {
    try {
      const res = await fetch(url, { headers });
      if (res.status === 429) {
        const wait = rateLimit.backoffMs * attempt;
        log(`Rate limited (429), waiting ${wait}ms... (attempt ${attempt}/${rateLimit.retries})`, "warning");
        await sleep(wait);
        continue;
      }
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${(await res.text()).slice(0, 200)}`);
      }
      return await res.json();
    } catch (err) {
      if (attempt === rateLimit.retries) throw err;
      const wait = rateLimit.backoffMs * attempt;
      log(`Request failed (attempt ${attempt}/${rateLimit.retries}): ${err.message}. Retrying in ${wait}ms...`, "warning");
      await sleep(wait);
    }
  }
}

/**
 * POST request with retry and rate-limit handling.
 *
 * @param {string} url - Full URL to fetch
 * @param {object} body - Request body (will be JSON-stringified)
 * @param {object} headers - Auth headers
 * @param {object} [rateLimit] - { retries, backoffMs }
 * @returns {Promise<any>} Parsed JSON response
 */
export async function apiPost(url, body, headers, rateLimit = DEFAULT_RATE_LIMIT) {
  const postHeaders = { ...headers, "Content-Type": "application/json" };
  for (let attempt = 1; attempt <= rateLimit.retries; attempt++) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: postHeaders,
        body: JSON.stringify(body),
      });
      if (res.status === 429) {
        const wait = rateLimit.backoffMs * attempt;
        log(`Rate limited (429), waiting ${wait}ms... (attempt ${attempt}/${rateLimit.retries})`, "warning");
        await sleep(wait);
        continue;
      }
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${(await res.text()).slice(0, 200)}`);
      }
      return await res.json();
    } catch (err) {
      if (attempt === rateLimit.retries) throw err;
      const wait = rateLimit.backoffMs * attempt;
      log(`POST failed (attempt ${attempt}/${rateLimit.retries}): ${err.message}. Retrying in ${wait}ms...`, "warning");
      await sleep(wait);
    }
  }
}

// ─── Backup ─────────────────────────────────────────────────────────────────

/**
 * Create or overwrite a backup file with entries.
 * For small backups (image-alt, meta-tags, schema).
 */
export function createBackup(filepath, entries) {
  ensureDir(path.dirname(filepath));
  fs.writeFileSync(filepath, JSON.stringify(entries, null, 2));
}

/**
 * Load a backup file. Returns null if missing or corrupted.
 */
export function loadBackup(filepath) {
  if (!fs.existsSync(filepath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filepath, "utf-8"));
  } catch (err) {
    log(`Backup file corrupted (${filepath}): ${err.message}. Cannot restore from this backup.`, "warning");
    return null;
  }
}

/**
 * Append a single entry to a backup file (JSON format).
 * Loads existing backup, appends, and re-saves.
 * For small-to-medium backups only.
 */
export function appendBackup(filepath, entry) {
  const existing = loadBackup(filepath) || [];
  existing.push(entry);
  createBackup(filepath, existing);
}

/**
 * Append a single entry to an NDJSON backup file (newline-delimited JSON).
 * For large backups (internal-links post content, 50-100MB+).
 * Avoids loading entire file into memory.
 */
export function appendNDJSON(filepath, entry) {
  ensureDir(path.dirname(filepath));
  fs.appendFileSync(filepath, JSON.stringify(entry) + "\n");
}

/**
 * Stream-read an NDJSON backup file line by line.
 * Returns an async iterable of parsed entries.
 * Skips corrupted lines with a warning.
 *
 * @param {string} filepath
 * @returns {AsyncIterable<object>}
 */
export async function* readNDJSON(filepath) {
  if (!fs.existsSync(filepath)) return;
  const rl = readline.createInterface({
    input: createReadStream(filepath),
    crlfDelay: Infinity,
  });
  let lineNum = 0;
  for await (const line of rl) {
    lineNum++;
    if (!line.trim()) continue;
    try {
      yield JSON.parse(line);
    } catch {
      log(`Skipping corrupted line ${lineNum} in ${filepath}`, "warning");
    }
  }
}

// ─── State Management ───────────────────────────────────────────────────────

/**
 * Load execution state from a JSON file.
 * Returns default state if file doesn't exist.
 */
export function loadState(filepath, defaults = {}) {
  const state = loadJSON(filepath);
  if (state) return state;
  return {
    startTime: new Date().toISOString(),
    processed: [],
    failed: [],
    skipped: [],
    stats: { total: 0, updated: 0, skipped: 0, failed: 0 },
    ...defaults,
  };
}

/**
 * Save execution state to a JSON file.
 */
export function saveState(filepath, state) {
  saveJSON(filepath, state);
}

// ─── File Locking ───────────────────────────────────────────────────────────

export class LockError extends Error {
  constructor(message, lockData) {
    super(message);
    this.name = "LockError";
    this.lockData = lockData;
  }
}

/**
 * Acquire a global lock. Throws LockError if lock is held by another process.
 *
 * @param {string} lockPath - Path to lock file
 * @param {number} [ttlMs=28800000] - Lock TTL in ms (default 8 hours)
 */
export function acquireGlobalLock(lockPath, ttlMs = 8 * 3600 * 1000) {
  ensureDir(path.dirname(lockPath));
  if (fs.existsSync(lockPath)) {
    try {
      const lockData = JSON.parse(fs.readFileSync(lockPath, "utf-8"));
      const age = Date.now() - lockData.timestamp;
      if (age < ttlMs) {
        throw new LockError(
          `Lock held (age: ${Math.round(age / 1000)}s, pid: ${lockData.pid}). Another SEO operation may be running.`,
          lockData
        );
      }
      log("Removing stale lock file", "warning");
    } catch (e) {
      if (e instanceof LockError) throw e;
      // Corrupted lock file — remove it
      log("Removing corrupted lock file", "warning");
    }
  }
  fs.writeFileSync(
    lockPath,
    JSON.stringify({ timestamp: Date.now(), pid: process.pid, startedAt: new Date().toISOString() }, null, 2)
  );
  log("Lock acquired", "success");
}

/**
 * Release a global lock.
 */
export function releaseGlobalLock(lockPath) {
  if (fs.existsSync(lockPath)) {
    try {
      fs.unlinkSync(lockPath);
      log("Lock released", "success");
    } catch (e) {
      log(`Failed to release lock: ${e.message}`, "warning");
    }
  }
}

// ─── Common Utilities ───────────────────────────────────────────────────────

export function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

export function saveJSON(filepath, data) {
  ensureDir(path.dirname(filepath));
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
}

export function loadJSON(filepath) {
  if (!fs.existsSync(filepath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filepath, "utf-8"));
  } catch (err) {
    log(`Failed to parse JSON (${filepath}): ${err.message}`, "warning");
    return null;
  }
}

export function log(msg, level = "info") {
  const ts = new Date().toISOString().split("T")[1].slice(0, 8);
  const prefix = {
    info: "ℹ️",
    success: "✅",
    error: "❌",
    warning: "⚠️",
    skip: "⏭️",
  }[level] || "  ";
  console.log(`[${ts}] ${prefix} ${msg}`);
}

/**
 * Check if an alt text looks like a filename (weak/missing).
 */
export function isFilenameLikeAlt(alt) {
  if (!alt || alt.trim() === "") return true;
  return /^(IMG|DSC|Screenshot|DSCF|P\d|image|photo|pic)[-_\s]?\d*/i.test(alt.trim());
}

// ─── Site Config Helper ─────────────────────────────────────────────────────

/**
 * Load site config from site-optimizer-config.json.
 *
 * @param {string} siteName - Site key (e.g., "yololab")
 * @param {string} [rootDir] - Project root
 * @returns {object|null} Site config or null if not found
 */
export function loadSiteConfig(siteName, rootDir = process.cwd()) {
  const configPath = path.join(rootDir, ".claude/skills/site-optimizer-config.json");
  const config = loadJSON(configPath);
  if (!config?.siteConfig?.[siteName]) {
    log(`Site "${siteName}" not found in config`, "error");
    return null;
  }
  return config.siteConfig[siteName];
}

// ─── Default Rate Limit Export ──────────────────────────────────────────────

export { DEFAULT_RATE_LIMIT };
