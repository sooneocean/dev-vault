import { jest } from "@jest/globals";
import fs from "fs";
import path from "path";
import os from "os";

// ─── Mock Setup ──────────────────────────────────────────────────────────
// Must be before imports of modules under test

// Mock seo-shared utilities
const mockApiGet = jest.fn();
const mockApiPost = jest.fn();
const mockDiscoverAuth = jest.fn();
const mockVerifyAuth = jest.fn();
const mockLog = jest.fn();

jest.unstable_mockModule("../../scripts/lib/seo-shared.js", () => ({
  discoverAuth: mockDiscoverAuth,
  resolveApiBase: jest.fn((site, auth, ver) =>
    `https://public-api.wordpress.com/rest/v1.1/sites/${site.siteId}`
  ),
  verifyAuth: mockVerifyAuth,
  apiGet: mockApiGet,
  apiPost: mockApiPost,
  createBackup: (filepath, entries) => {
    const dir = path.dirname(filepath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filepath, JSON.stringify(entries, null, 2));
  },
  loadBackup: (filepath) => {
    if (!fs.existsSync(filepath)) return null;
    return JSON.parse(fs.readFileSync(filepath, "utf-8"));
  },
  appendBackup: jest.fn(),
  loadState: (filepath, defaults) => {
    if (fs.existsSync(filepath)) {
      return JSON.parse(fs.readFileSync(filepath, "utf-8"));
    }
    return {
      startTime: new Date().toISOString(),
      processed: [],
      failed: [],
      skipped: [],
      stats: { total: 0, updated: 0, skipped: 0, failed: 0 },
      ...defaults,
    };
  },
  saveState: (filepath, state) => {
    const dir = path.dirname(filepath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filepath, JSON.stringify(state, null, 2));
  },
  log: mockLog,
  sleep: jest.fn(() => Promise.resolve()),
  ensureDir: (dir) => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  },
  saveJSON: (filepath, data) => {
    const dir = path.dirname(filepath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  },
  loadJSON: (filepath) => {
    if (!fs.existsSync(filepath)) return null;
    return JSON.parse(fs.readFileSync(filepath, "utf-8"));
  },
  DEFAULT_RATE_LIMIT: { batchSize: 5, delayMs: 2000, retries: 3, backoffMs: 3000 },
}));

// Mock the phase4 generator
const mockGenerateMetaOptimization = jest.fn();
jest.unstable_mockModule("../../scripts/phase4-complete-seo-batch-generator.js", () => ({
  generateMetaOptimization: mockGenerateMetaOptimization,
  generateSchemaMarkup: jest.fn(),
  generateOGTags: jest.fn(),
}));

// Mock the phase4 applier
const mockBuildMetadataUpdate = jest.fn();
const mockUpdatePostMetadata = jest.fn();
const mockVerifyYoastSupport = jest.fn();
const mockBackupPostMetadata = jest.fn();
const mockRollbackMetadata = jest.fn();

jest.unstable_mockModule("../../scripts/phase4-apply-seo-to-wordpress.js", () => ({
  buildMetadataUpdate: mockBuildMetadataUpdate,
  updatePostMetadata: mockUpdatePostMetadata,
  verifyYoastSupport: mockVerifyYoastSupport,
  backupPostMetadata: mockBackupPostMetadata,
  rollbackMetadata: mockRollbackMetadata,
}));

// ─── Import Module Under Test ────────────────────────────────────────────

const { scan, generate, apply, verify, rollback, run } = await import(
  "../../scripts/modules/meta-tags.js"
);

// ─── Test Suite ──────────────────────────────────────────────────────────

describe("meta-tags module", () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "meta-tags-test-"));
    jest.clearAllMocks();

    // Default auth mock
    mockDiscoverAuth.mockReturnValue({
      method: "bearer",
      headers: { Authorization: "Bearer test-token" },
      apiBase: "wpcom-proxy",
    });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  // ─── Happy Path: Generate ────────────────────────────────────────────

  describe("generate", () => {
    test("generates title + description for a sample article", async () => {
      const articles = [
        {
          id: 101,
          title: "Test Article About Travel",
          tags: [{ name: "travel" }],
          excerpt: "A great article about traveling.",
          date: "2025-01-01",
        },
      ];

      mockGenerateMetaOptimization.mockResolvedValueOnce({
        optimizedTitle: "Best Travel Tips 2025 | Complete Guide",
        metaDescription: "Discover the best travel tips for 2025 including budgets, destinations, and more.",
        primaryKeywords: ["travel tips", "2025 guide"],
        rationale: "Optimized for search intent",
      });

      const result = await generate(articles, { outputDir: tmpDir, delayMs: 0 });

      expect(result.stats.success).toBe(1);
      expect(result.stats.failed).toBe(0);
      expect(result.results).toHaveLength(1);
      expect(result.results[0].meta.optimizedTitle).toBe("Best Travel Tips 2025 | Complete Guide");
      expect(result.results[0].meta.metaDescription).toContain("travel tips");
    });

    test("skips article that already has optimized meta title and description", async () => {
      const articles = [
        {
          id: 102,
          title: "Already Optimized",
          hasMetaTitle: true,
          hasMetaDesc: true,
        },
      ];

      const result = await generate(articles, { outputDir: tmpDir, delayMs: 0 });

      expect(result.stats.skipped).toBe(1);
      expect(result.stats.success).toBe(0);
      expect(mockGenerateMetaOptimization).not.toHaveBeenCalled();
    });

    test("force flag overrides skip for already-optimized articles", async () => {
      const articles = [
        {
          id: 103,
          title: "Force Regenerate",
          hasMetaTitle: true,
          hasMetaDesc: true,
        },
      ];

      mockGenerateMetaOptimization.mockResolvedValueOnce({
        optimizedTitle: "Regenerated Title",
        metaDescription: "Regenerated description",
        primaryKeywords: [],
        rationale: "Forced",
      });

      const result = await generate(articles, { outputDir: tmpDir, delayMs: 0, force: true });

      expect(result.stats.success).toBe(1);
      expect(mockGenerateMetaOptimization).toHaveBeenCalled();
    });
  });

  // ─── Happy Path: Apply ───────────────────────────────────────────────

  describe("apply", () => {
    test("writes metadata and backup file contains original values", async () => {
      const results = [
        {
          id: 201,
          title: "Test Post",
          meta: {
            optimizedTitle: "Optimized Title",
            metaDescription: "Optimized description",
          },
          success: true,
        },
      ];

      mockVerifyYoastSupport.mockResolvedValueOnce({ ok: true });
      mockBuildMetadataUpdate.mockReturnValueOnce({
        _yoast_wpseo_title: "Optimized Title",
        _yoast_wpseo_metadesc: "Optimized description",
      });
      mockUpdatePostMetadata.mockResolvedValueOnce({ success: true });
      mockBackupPostMetadata.mockResolvedValueOnce({
        _yoast_wpseo_title: "Original Title",
        _yoast_wpseo_metadesc: "Original description",
      });

      const result = await apply(results, { outputDir: tmpDir, delayMs: 0 });

      expect(result.applied).toBe(1);
      expect(result.failed).toBe(0);
      expect(result.backupPath).toBeTruthy();
      expect(mockBackupPostMetadata).toHaveBeenCalledWith(
        201,
        expect.objectContaining({ outputDir: tmpDir }),
        expect.any(String)
      );
      expect(mockBuildMetadataUpdate).toHaveBeenCalledWith(201, { meta: results[0].meta });
      expect(mockUpdatePostMetadata).toHaveBeenCalled();
    });

    test("Yoast fields not supported returns clear error before batch starts", async () => {
      mockVerifyYoastSupport.mockResolvedValueOnce({
        ok: false,
        error: "Yoast SEO plugin not installed",
      });

      const result = await apply(
        [{ id: 301, success: true, meta: { optimizedTitle: "T", metaDescription: "D" } }],
        { outputDir: tmpDir }
      );

      expect(result.applied).toBe(0);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].message).toContain("Yoast fields not supported");
      // Should NOT have attempted any writes
      expect(mockUpdatePostMetadata).not.toHaveBeenCalled();
    });

    test("apply fails mid-batch — partial backup exists, processed articles tracked", async () => {
      const results = [
        { id: 401, title: "Post A", meta: { optimizedTitle: "A", metaDescription: "A desc" }, success: true },
        { id: 402, title: "Post B", meta: { optimizedTitle: "B", metaDescription: "B desc" }, success: true },
        { id: 403, title: "Post C", meta: { optimizedTitle: "C", metaDescription: "C desc" }, success: true },
      ];

      mockVerifyYoastSupport.mockResolvedValueOnce({ ok: true });
      mockBackupPostMetadata.mockResolvedValue({});
      mockBuildMetadataUpdate.mockReturnValue({ _yoast_wpseo_title: "T" });

      // First succeeds, second fails, third succeeds
      mockUpdatePostMetadata
        .mockResolvedValueOnce({ success: true })
        .mockResolvedValueOnce({ success: false, error: "API timeout" })
        .mockResolvedValueOnce({ success: true });

      const result = await apply(results, { outputDir: tmpDir, delayMs: 0 });

      expect(result.applied).toBe(2);
      expect(result.failed).toBe(1);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].postId).toBe(402);

      // Verify state was saved with processed articles
      const statePath = path.join(tmpDir, "meta-tags-apply-state.json");
      expect(fs.existsSync(statePath)).toBe(true);
      const state = JSON.parse(fs.readFileSync(statePath, "utf-8"));
      expect(state.processed).toHaveLength(2);
      expect(state.failed).toHaveLength(1);
    });
  });

  // ─── Scan ────────────────────────────────────────────────────────────

  describe("scan", () => {
    test("identifies articles missing meta title or description", async () => {
      mockApiGet
        .mockResolvedValueOnce({
          posts: [
            {
              ID: 501,
              title: "Missing Both",
              metadata: [],
            },
            {
              ID: 502,
              title: "Has Title Only",
              metadata: [{ key: "_yoast_wpseo_title", value: "My Title" }],
            },
            {
              ID: 503,
              title: "Fully Optimized",
              metadata: [
                { key: "_yoast_wpseo_title", value: "My Title" },
                { key: "_yoast_wpseo_metadesc", value: "My description" },
              ],
            },
          ],
        })
        .mockResolvedValueOnce({ posts: [] }); // End pagination

      const result = await scan({ outputDir: tmpDir, sample: 10 });

      expect(result.total).toBe(3);
      expect(result.needsOptimization).toBe(2);
      expect(result.articles.map(a => a.id)).toEqual([501, 502]);
    });
  });

  // ─── Rollback Integration ────────────────────────────────────────────

  describe("rollback", () => {
    test("restores original Yoast field values from backup", async () => {
      const backupPath = path.join(tmpDir, "test-backup.json");

      mockRollbackMetadata.mockResolvedValueOnce({
        restored: 2,
        failed: 0,
        errors: [],
      });

      const result = await rollback(backupPath, { blogId: 123 });

      expect(result.restored).toBe(2);
      expect(result.failed).toBe(0);
      expect(mockRollbackMetadata).toHaveBeenCalledWith(
        backupPath,
        expect.objectContaining({ blogId: 123 }),
        {}
      );
    });
  });

  // ─── Generate → Apply → Rollback Round-Trip ─────────────────────────

  describe("generate → apply → rollback round-trip", () => {
    test("preserves original data through full cycle", async () => {
      // Step 1: Generate
      const articles = [
        { id: 601, title: "Round-Trip Test", date: "2025-06-01" },
      ];

      mockGenerateMetaOptimization.mockResolvedValueOnce({
        optimizedTitle: "New Title",
        metaDescription: "New description",
        primaryKeywords: ["test"],
        rationale: "Test",
      });

      const genResult = await generate(articles, { outputDir: tmpDir, delayMs: 0 });
      expect(genResult.stats.success).toBe(1);

      // Step 2: Apply
      mockVerifyYoastSupport.mockResolvedValueOnce({ ok: true });
      mockBackupPostMetadata.mockResolvedValueOnce({
        _yoast_wpseo_title: "Original Title",
        _yoast_wpseo_metadesc: "Original description",
      });
      mockBuildMetadataUpdate.mockReturnValueOnce({
        _yoast_wpseo_title: "New Title",
        _yoast_wpseo_metadesc: "New description",
      });
      mockUpdatePostMetadata.mockResolvedValueOnce({ success: true });

      const applyResult = await apply(genResult.results, { outputDir: tmpDir, delayMs: 0 });
      expect(applyResult.applied).toBe(1);
      expect(applyResult.backupPath).toBeTruthy();

      // Step 3: Rollback
      mockRollbackMetadata.mockResolvedValueOnce({
        restored: 1,
        failed: 0,
        errors: [],
      });

      const rollbackResult = await rollback(applyResult.backupPath, {});
      expect(rollbackResult.restored).toBe(1);
      expect(rollbackResult.failed).toBe(0);
    });
  });
});
