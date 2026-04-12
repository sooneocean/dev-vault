import { jest } from "@jest/globals";
import fs from "fs";
import path from "path";
import os from "os";
import {
  loadOrchestratorState,
  saveOrchestratorState,
  clearOrchestratorState,
  checkSessionStatus,
  loadAuditCache,
  saveAuditCache,
  isAuditCacheFresh,
  getOrchestratorPaths,
} from "../scripts/lib/seo-orchestrator-state.js";

describe("seo-orchestrator-state", () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "seo-orch-test-"));
    // Create the output directory structure
    fs.mkdirSync(path.join(tmpDir, "seo-optimization-output"), { recursive: true });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe("orchestrator state", () => {
    it("saves and loads state correctly with all fields", () => {
      const state = {
        activeModule: "image-alt",
        batchId: "batch-001",
        startTime: "2026-04-12T10:00:00.000Z",
        articlesProcessed: 50,
        articlesRemaining: 200,
        userIntent: "optimize all image alt texts",
      };

      saveOrchestratorState(state, tmpDir);
      const loaded = loadOrchestratorState(tmpDir);

      expect(loaded.activeModule).toBe("image-alt");
      expect(loaded.batchId).toBe("batch-001");
      expect(loaded.articlesProcessed).toBe(50);
      expect(loaded.articlesRemaining).toBe(200);
      expect(loaded.userIntent).toBe("optimize all image alt texts");
      expect(loaded.lastUpdated).toBeDefined();
    });

    it("returns null when no state file exists", () => {
      const loaded = loadOrchestratorState(tmpDir);
      expect(loaded).toBeNull();
    });

    it("clears state file", () => {
      saveOrchestratorState({ activeModule: "test" }, tmpDir);
      expect(loadOrchestratorState(tmpDir)).not.toBeNull();

      clearOrchestratorState(tmpDir);
      expect(loadOrchestratorState(tmpDir)).toBeNull();
    });

    it("clearOrchestratorState is safe when no state exists", () => {
      expect(() => clearOrchestratorState(tmpDir)).not.toThrow();
    });
  });

  describe("checkSessionStatus", () => {
    it("detects interrupted batch", () => {
      const state = {
        activeModule: "meta-tags",
        articlesProcessed: 100,
        articlesRemaining: 150,
        lastUpdated: new Date().toISOString(),
      };

      const status = checkSessionStatus(state);
      expect(status.interrupted).toBe(true);
      expect(status.stale).toBe(false);
      expect(status.module).toBe("meta-tags");
      expect(status.progress).toBe("100/250");
    });

    it("detects stale state (>24h)", () => {
      const state = {
        activeModule: "schema-markup",
        articlesProcessed: 10,
        articlesRemaining: 50,
        lastUpdated: new Date(Date.now() - 25 * 3600 * 1000).toISOString(),
      };

      const status = checkSessionStatus(state);
      expect(status.interrupted).toBe(true);
      expect(status.stale).toBe(true);
      expect(status.module).toBe("schema-markup");
    });

    it("returns not interrupted for null state", () => {
      const status = checkSessionStatus(null);
      expect(status.interrupted).toBe(false);
      expect(status.stale).toBe(false);
    });

    it("returns not interrupted for completed state", () => {
      const state = {
        activeModule: "image-alt",
        articlesProcessed: 100,
        articlesRemaining: 0,
        lastUpdated: new Date().toISOString(),
      };

      const status = checkSessionStatus(state);
      expect(status.interrupted).toBe(false);
    });
  });

  describe("audit cache", () => {
    it("saves and loads audit cache", () => {
      const auditData = {
        imageAlt: { total: 2728, missing: 500, weak: 200 },
        metaTags: { total: 2728, missing: 1500, weak: 300 },
        schema: { total: 2728, missing: 2000 },
        links: { total: 2728, missing: 800 },
      };

      saveAuditCache(auditData, tmpDir);
      const loaded = loadAuditCache(tmpDir);

      expect(loaded.timestamp).toBeDefined();
      expect(loaded.modules.imageAlt.missing).toBe(500);
      expect(loaded.modules.metaTags.missing).toBe(1500);
    });

    it("returns null for missing cache", () => {
      expect(loadAuditCache(tmpDir)).toBeNull();
    });

    it("isAuditCacheFresh returns true for recent cache", () => {
      const cache = { timestamp: new Date().toISOString(), modules: {} };
      expect(isAuditCacheFresh(cache)).toBe(true);
    });

    it("isAuditCacheFresh returns false for old cache (>7 days)", () => {
      const cache = {
        timestamp: new Date(Date.now() - 8 * 24 * 3600 * 1000).toISOString(),
        modules: {},
      };
      expect(isAuditCacheFresh(cache)).toBe(false);
    });

    it("isAuditCacheFresh returns false for null cache", () => {
      expect(isAuditCacheFresh(null)).toBe(false);
    });

    it("isAuditCacheFresh supports custom max age", () => {
      const cache = {
        timestamp: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(),
        modules: {},
      };
      expect(isAuditCacheFresh(cache, 1)).toBe(false);
      expect(isAuditCacheFresh(cache, 3)).toBe(true);
    });
  });

  describe("getOrchestratorPaths", () => {
    it("returns all expected paths", () => {
      const paths = getOrchestratorPaths(tmpDir);
      expect(paths.outputDir).toContain("seo-optimization-output");
      expect(paths.statePath).toContain("seo-orchestrator-state.json");
      expect(paths.auditCachePath).toContain("audit-cache.json");
      expect(paths.lockPath).toContain("seo-orchestrator.lock");
      expect(paths.backupsDir).toContain("backups");
    });
  });
});
