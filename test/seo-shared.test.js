import { jest } from "@jest/globals";
import fs from "fs";
import path from "path";
import os from "os";
import {
  discoverAuth,
  resolveApiBase,
  apiGet,
  apiPost,
  createBackup,
  loadBackup,
  appendBackup,
  appendNDJSON,
  readNDJSON,
  loadState,
  saveState,
  acquireGlobalLock,
  releaseGlobalLock,
  LockError,
  ensureDir,
  saveJSON,
  loadJSON,
  isFilenameLikeAlt,
} from "../scripts/lib/seo-shared.js";

describe("seo-shared utilities", () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "seo-test-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  // ─── Auth Discovery ─────────────────────────────────────────────────────

  describe("discoverAuth", () => {
    const originalEnv = { ...process.env };

    beforeEach(() => {
      delete process.env.WPCOM_TOKEN;
      delete process.env.WP_BEARER_TOKEN;
      delete process.env.WP_APP_USER;
      delete process.env.WP_APP_PASS;
      delete process.env.WP_USERNAME;
      delete process.env.WP_APP_PASSWORD;
    });

    afterEach(() => {
      process.env = { ...originalEnv };
    });

    test("returns bearer auth from WPCOM_TOKEN", () => {
      process.env.WPCOM_TOKEN = "test-token-123";
      const auth = discoverAuth({ rootDir: tmpDir });
      expect(auth).not.toBeNull();
      expect(auth.method).toBe("bearer");
      expect(auth.headers.Authorization).toBe("Bearer test-token-123");
      expect(auth.apiBase).toBe("wpcom-proxy");
    });

    test("returns bearer auth from WP_BEARER_TOKEN when WPCOM_TOKEN missing", () => {
      process.env.WP_BEARER_TOKEN = "bearer-token-456";
      const auth = discoverAuth({ rootDir: tmpDir });
      expect(auth.method).toBe("bearer");
      expect(auth.headers.Authorization).toBe("Bearer bearer-token-456");
    });

    test("returns basic auth from WP_APP_USER + WP_APP_PASS", () => {
      process.env.WP_APP_USER = "myuser";
      process.env.WP_APP_PASS = "mypass";
      const auth = discoverAuth({ rootDir: tmpDir });
      expect(auth.method).toBe("basic");
      expect(auth.headers.Authorization).toMatch(/^Basic /);
      expect(auth.apiBase).toBe("direct");
    });

    test("returns null with no credentials", () => {
      const auth = discoverAuth({ rootDir: tmpDir });
      expect(auth).toBeNull();
    });

    test("reads bearer token from .env file", () => {
      fs.writeFileSync(path.join(tmpDir, ".env"), "WPCOM_TOKEN=env-file-token\n");
      const auth = discoverAuth({ rootDir: tmpDir });
      expect(auth.method).toBe("bearer");
      expect(auth.headers.Authorization).toBe("Bearer env-file-token");
    });

    test("reads token from .mcp.json as last resort", () => {
      const mcpConfig = {
        mcpServers: {
          "wpcom-mcp": {
            headers: { Authorization: "Bearer mcp-token-789" },
          },
        },
      };
      fs.writeFileSync(path.join(tmpDir, ".mcp.json"), JSON.stringify(mcpConfig));
      const auth = discoverAuth({ rootDir: tmpDir });
      expect(auth.method).toBe("bearer");
      expect(auth.headers.Authorization).toBe("Bearer mcp-token-789");
    });
  });

  // ─── resolveApiBase ─────────────────────────────────────────────────────

  describe("resolveApiBase", () => {
    const siteConfig = { siteId: 12345, domain: "example.com" };

    test("returns direct wp-json URL for basic auth", () => {
      const url = resolveApiBase(siteConfig, { apiBase: "direct" });
      expect(url).toBe("https://example.com/wp-json/wp/v2");
    });

    test("returns wpcom proxy URL for bearer auth", () => {
      const url = resolveApiBase(siteConfig, { apiBase: "wpcom-proxy" });
      expect(url).toBe("https://public-api.wordpress.com/wp/v2/sites/12345");
    });

    test("returns v1.1 URL when requested", () => {
      const url = resolveApiBase(siteConfig, { apiBase: "wpcom-proxy" }, "v1.1");
      expect(url).toBe("https://public-api.wordpress.com/rest/v1.1/sites/12345");
    });
  });

  // ─── API Helpers ────────────────────────────────────────────────────────

  describe("apiGet", () => {
    const _origFetch = global.fetch;

    afterEach(() => {
      global.fetch = _origFetch;
    });

    test("fetches successfully on first try", async () => {
      const mockData = { id: 1, title: "Test" };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockData),
      });

      const result = await apiGet("https://example.com/api", {});
      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    test("retries on 429 and succeeds on 3rd attempt", async () => {
      const mockData = { id: 1 };
      global.fetch = jest.fn()
        .mockResolvedValueOnce({ ok: false, status: 429 })
        .mockResolvedValueOnce({ ok: false, status: 429 })
        .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve(mockData) });

      const result = await apiGet("https://example.com/api", {}, { retries: 3, backoffMs: 10 });
      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledTimes(3);
    });

    test("throws after exhausting all retries", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: () => Promise.resolve("Internal Server Error"),
      });

      await expect(
        apiGet("https://example.com/api", {}, { retries: 3, backoffMs: 10 })
      ).rejects.toThrow("HTTP 500");
      expect(global.fetch).toHaveBeenCalledTimes(3);
    });
  });

  describe("apiPost", () => {
    const _origFetch = global.fetch;

    afterEach(() => {
      global.fetch = _origFetch;
    });

    test("retries on network failure and succeeds", async () => {
      const mockData = { success: true };
      global.fetch = jest.fn()
        .mockRejectedValueOnce(new Error("ECONNRESET"))
        .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve(mockData) });

      const result = await apiPost(
        "https://example.com/api",
        { title: "test" },
        {},
        { retries: 3, backoffMs: 10 }
      );
      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  // ─── Backup ─────────────────────────────────────────────────────────────

  describe("backup operations", () => {
    test("createBackup and loadBackup round-trip", () => {
      const filepath = path.join(tmpDir, "backup.json");
      const entries = [{ id: 1, original: "old" }, { id: 2, original: "old2" }];
      createBackup(filepath, entries);
      const loaded = loadBackup(filepath);
      expect(loaded).toEqual(entries);
    });

    test("loadBackup returns null for missing file", () => {
      expect(loadBackup(path.join(tmpDir, "nonexistent.json"))).toBeNull();
    });

    test("loadBackup returns null for corrupted file", () => {
      const filepath = path.join(tmpDir, "corrupted.json");
      fs.writeFileSync(filepath, "{ broken json");
      expect(loadBackup(filepath)).toBeNull();
    });

    test("appendBackup adds entries incrementally", () => {
      const filepath = path.join(tmpDir, "append-backup.json");
      appendBackup(filepath, { id: 1, val: "a" });
      appendBackup(filepath, { id: 2, val: "b" });
      const loaded = loadBackup(filepath);
      expect(loaded).toHaveLength(2);
      expect(loaded[1]).toEqual({ id: 2, val: "b" });
    });
  });

  // ─── NDJSON ─────────────────────────────────────────────────────────────

  describe("NDJSON operations", () => {
    test("appendNDJSON and readNDJSON round-trip", async () => {
      const filepath = path.join(tmpDir, "backup.ndjson");
      appendNDJSON(filepath, { id: 1, content: "hello" });
      appendNDJSON(filepath, { id: 2, content: "world" });

      const entries = [];
      for await (const entry of readNDJSON(filepath)) {
        entries.push(entry);
      }
      expect(entries).toHaveLength(2);
      expect(entries[0]).toEqual({ id: 1, content: "hello" });
      expect(entries[1]).toEqual({ id: 2, content: "world" });
    });

    test("readNDJSON skips corrupted lines", async () => {
      const filepath = path.join(tmpDir, "mixed.ndjson");
      fs.writeFileSync(filepath, '{"id":1}\n{broken}\n{"id":3}\n');

      const entries = [];
      for await (const entry of readNDJSON(filepath)) {
        entries.push(entry);
      }
      expect(entries).toHaveLength(2);
      expect(entries[0].id).toBe(1);
      expect(entries[1].id).toBe(3);
    });

    test("readNDJSON returns empty for missing file", async () => {
      const entries = [];
      for await (const entry of readNDJSON(path.join(tmpDir, "nope.ndjson"))) {
        entries.push(entry);
      }
      expect(entries).toHaveLength(0);
    });
  });

  // ─── State Management ─────────────────────────────────────────────────

  describe("state management", () => {
    test("saveState and loadState round-trip", () => {
      const filepath = path.join(tmpDir, "state.json");
      const state = { processed: [1, 2], failed: [3], stats: { total: 3 } };
      saveState(filepath, state);
      const loaded = loadState(filepath);
      expect(loaded).toEqual(state);
    });

    test("loadState returns defaults for missing file", () => {
      const filepath = path.join(tmpDir, "missing-state.json");
      const state = loadState(filepath, { name: "test" });
      expect(state.processed).toEqual([]);
      expect(state.failed).toEqual([]);
      expect(state.name).toBe("test");
      expect(state.startTime).toBeDefined();
    });
  });

  // ─── File Locking ─────────────────────────────────────────────────────

  describe("global lock", () => {
    test("acquires and releases lock successfully", () => {
      const lockPath = path.join(tmpDir, "test.lock");
      acquireGlobalLock(lockPath);
      expect(fs.existsSync(lockPath)).toBe(true);

      releaseGlobalLock(lockPath);
      expect(fs.existsSync(lockPath)).toBe(false);
    });

    test("throws LockError when lock is fresh", () => {
      const lockPath = path.join(tmpDir, "test.lock");
      acquireGlobalLock(lockPath);

      expect(() => acquireGlobalLock(lockPath)).toThrow(LockError);
    });

    test("acquires lock when existing lock is stale", () => {
      const lockPath = path.join(tmpDir, "test.lock");
      fs.writeFileSync(lockPath, JSON.stringify({ timestamp: Date.now() - 100000, pid: 99999 }));

      expect(() => acquireGlobalLock(lockPath, 1000)).not.toThrow();
    });
  });

  // ─── Utility Functions ────────────────────────────────────────────────

  describe("utility functions", () => {
    test("ensureDir creates nested directories", () => {
      const dir = path.join(tmpDir, "a", "b", "c");
      ensureDir(dir);
      expect(fs.existsSync(dir)).toBe(true);
    });

    test("saveJSON and loadJSON round-trip", () => {
      const filepath = path.join(tmpDir, "data.json");
      saveJSON(filepath, { key: "value" });
      expect(loadJSON(filepath)).toEqual({ key: "value" });
    });

    test("loadJSON returns null for missing file", () => {
      expect(loadJSON(path.join(tmpDir, "nope.json"))).toBeNull();
    });

    test("isFilenameLikeAlt detects filename patterns", () => {
      expect(isFilenameLikeAlt("")).toBe(true);
      expect(isFilenameLikeAlt(null)).toBe(true);
      expect(isFilenameLikeAlt("IMG_2034")).toBe(true);
      expect(isFilenameLikeAlt("DSC00123")).toBe(true);
      expect(isFilenameLikeAlt("Screenshot 2024")).toBe(true);
      expect(isFilenameLikeAlt("A beautiful sunset over the ocean")).toBe(false);
    });
  });
});
