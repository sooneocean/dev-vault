import { jest } from "@jest/globals";
import fs from "fs";
import path from "path";
import os from "os";

// ─── Mock Setup ──────────────────────────────────────────────────────────

const mockApiGet = jest.fn();
const mockApiPost = jest.fn();
const mockDiscoverAuth = jest.fn();
const mockLog = jest.fn();

jest.unstable_mockModule("../../scripts/lib/seo-shared.js", () => ({
  discoverAuth: mockDiscoverAuth,
  resolveApiBase: jest.fn(),
  verifyAuth: jest.fn(),
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
const mockGenerateSchemaMarkup = jest.fn();
jest.unstable_mockModule("../../scripts/phase4-complete-seo-batch-generator.js", () => ({
  generateMetaOptimization: jest.fn(),
  generateSchemaMarkup: mockGenerateSchemaMarkup,
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
  "../../scripts/modules/schema-markup.js"
);

// ─── Test Suite ──────────────────────────────────────────────────────────

describe("schema-markup module", () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "schema-test-"));
    jest.clearAllMocks();

    mockDiscoverAuth.mockReturnValue({
      method: "bearer",
      headers: { Authorization: "Bearer test-token" },
      apiBase: "wpcom-proxy",
    });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  // ─── Happy Path: Generate JSON-LD ────────────────────────────────────

  describe("generate", () => {
    test("generates JSON-LD schema for a sample article", async () => {
      const articles = [
        {
          id: 101,
          title: "Movie Review: Inception",
          tags: [{ name: "movie" }, { name: "review" }],
          date: "2025-03-15",
          modified: "2025-03-16",
          excerpt: "A deep dive into Christopher Nolan's masterpiece.",
        },
      ];

      const mockSchema = {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: "Movie Review: Inception",
        description: "A deep dive into Christopher Nolan's masterpiece.",
        datePublished: "2025-03-15",
        dateModified: "2025-03-16",
        author: { "@type": "Person", name: "YOLO LAB" },
        publisher: { "@type": "Organization", name: "YOLO LAB" },
      };

      mockGenerateSchemaMarkup.mockResolvedValueOnce(mockSchema);

      const result = await generate(articles, { outputDir: tmpDir, delayMs: 0 });

      expect(result.stats.success).toBe(1);
      expect(result.stats.failed).toBe(0);
      expect(result.results).toHaveLength(1);
      expect(result.results[0].schema["@context"]).toBe("https://schema.org");
      expect(result.results[0].schema["@type"]).toBe("Article");
      expect(result.results[0].schema.headline).toBe("Movie Review: Inception");
    });

    test("skips article that already has valid schema", async () => {
      const articles = [
        {
          id: 102,
          title: "Already Has Schema",
          hasSchema: true,
          isValidSchema: true,
        },
      ];

      const result = await generate(articles, { outputDir: tmpDir, delayMs: 0 });

      expect(result.stats.skipped).toBe(1);
      expect(result.stats.success).toBe(0);
      expect(mockGenerateSchemaMarkup).not.toHaveBeenCalled();
    });

    test("handles generation failure gracefully", async () => {
      const articles = [
        { id: 103, title: "Failing Article", date: "2025-01-01" },
      ];

      mockGenerateSchemaMarkup.mockRejectedValueOnce(new Error("Claude API rate limit"));

      const result = await generate(articles, { outputDir: tmpDir, delayMs: 0 });

      expect(result.stats.failed).toBe(1);
      expect(result.stats.success).toBe(0);
      expect(result.results[0].success).toBe(false);
      expect(result.results[0].error).toContain("rate limit");
    });
  });

  // ─── Happy Path: Apply ───────────────────────────────────────────────

  describe("apply", () => {
    test("writes schema metadata and creates backup", async () => {
      const schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: "Test",
      };

      const results = [
        { id: 201, title: "Test Post", schema, success: true },
      ];

      mockVerifyYoastSupport.mockResolvedValueOnce({ ok: true });
      mockBuildMetadataUpdate.mockReturnValueOnce({
        _yoast_wpseo_schema: JSON.stringify(schema),
      });
      mockUpdatePostMetadata.mockResolvedValueOnce({ success: true });
      mockBackupPostMetadata.mockResolvedValueOnce({
        _yoast_wpseo_schema: "",
      });

      const result = await apply(results, { outputDir: tmpDir, delayMs: 0 });

      expect(result.applied).toBe(1);
      expect(result.failed).toBe(0);
      expect(result.backupPath).toBeTruthy();
      expect(mockBackupPostMetadata).toHaveBeenCalled();
      expect(mockBuildMetadataUpdate).toHaveBeenCalledWith(201, { schema });
    });

    test("Yoast fields not supported returns clear error", async () => {
      mockVerifyYoastSupport.mockResolvedValueOnce({
        ok: false,
        error: "Yoast SEO not installed on this site",
      });

      const result = await apply(
        [{ id: 301, success: true, schema: { "@context": "https://schema.org", "@type": "Article" } }],
        { outputDir: tmpDir }
      );

      expect(result.applied).toBe(0);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].message).toContain("Yoast fields not supported");
      expect(mockUpdatePostMetadata).not.toHaveBeenCalled();
    });

    test("apply fails mid-batch — partial state tracked", async () => {
      const schema = { "@context": "https://schema.org", "@type": "Article" };
      const results = [
        { id: 401, title: "A", schema, success: true },
        { id: 402, title: "B", schema, success: true },
        { id: 403, title: "C", schema, success: true },
      ];

      mockVerifyYoastSupport.mockResolvedValueOnce({ ok: true });
      mockBackupPostMetadata.mockResolvedValue({});
      mockBuildMetadataUpdate.mockReturnValue({ _yoast_wpseo_schema: "{}" });

      mockUpdatePostMetadata
        .mockResolvedValueOnce({ success: true })
        .mockResolvedValueOnce({ success: false, error: "Server error 500" })
        .mockResolvedValueOnce({ success: true });

      const result = await apply(results, { outputDir: tmpDir, delayMs: 0 });

      expect(result.applied).toBe(2);
      expect(result.failed).toBe(1);
      expect(result.errors[0].postId).toBe(402);

      // State file should track progress
      const statePath = path.join(tmpDir, "schema-markup-apply-state.json");
      expect(fs.existsSync(statePath)).toBe(true);
      const state = JSON.parse(fs.readFileSync(statePath, "utf-8"));
      expect(state.processed).toHaveLength(2);
      expect(state.failed).toHaveLength(1);
    });
  });

  // ─── Scan ────────────────────────────────────────────────────────────

  describe("scan", () => {
    test("identifies articles missing schema markup", async () => {
      mockApiGet
        .mockResolvedValueOnce({
          posts: [
            {
              ID: 501,
              title: "No Schema",
              metadata: [],
            },
            {
              ID: 502,
              title: "Invalid Schema",
              metadata: [{ key: "_yoast_wpseo_schema", value: "not json" }],
            },
            {
              ID: 503,
              title: "Valid Schema",
              metadata: [{
                key: "_yoast_wpseo_schema",
                value: JSON.stringify({
                  "@context": "https://schema.org",
                  "@type": "Article",
                  headline: "Valid",
                }),
              }],
            },
          ],
        })
        .mockResolvedValueOnce({ posts: [] }); // End pagination

      const result = await scan({ outputDir: tmpDir, sample: 10 });

      expect(result.total).toBe(3);
      expect(result.needsOptimization).toBe(2);
      expect(result.articles.map(a => a.id)).toEqual([501, 502]);
      // The invalid schema article should have isValidSchema = false
      expect(result.articles[1].isValidSchema).toBe(false);
    });
  });

  // ─── Rollback ────────────────────────────────────────────────────────

  describe("rollback", () => {
    test("restores original schema values from backup", async () => {
      const backupPath = path.join(tmpDir, "schema-backup.json");

      mockRollbackMetadata.mockResolvedValueOnce({
        restored: 3,
        failed: 0,
        errors: [],
      });

      const result = await rollback(backupPath, { blogId: 456 });

      expect(result.restored).toBe(3);
      expect(result.failed).toBe(0);
      expect(mockRollbackMetadata).toHaveBeenCalledWith(
        backupPath,
        expect.objectContaining({ blogId: 456 }),
        {}
      );
    });
  });

  // ─── Generate → Apply → Rollback Round-Trip ─────────────────────────

  describe("generate → apply → rollback round-trip", () => {
    test("preserves original data through full cycle", async () => {
      // Step 1: Generate
      const articles = [
        {
          id: 601,
          title: "Round-Trip Schema Test",
          date: "2025-06-01",
          modified: "2025-06-02",
          tags: [{ name: "test" }],
        },
      ];

      const generatedSchema = {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: "Round-Trip Schema Test",
        datePublished: "2025-06-01",
        dateModified: "2025-06-02",
        author: { "@type": "Person", name: "YOLO LAB" },
      };

      mockGenerateSchemaMarkup.mockResolvedValueOnce(generatedSchema);

      const genResult = await generate(articles, { outputDir: tmpDir, delayMs: 0 });
      expect(genResult.stats.success).toBe(1);
      expect(genResult.results[0].schema["@type"]).toBe("Article");

      // Step 2: Apply
      mockVerifyYoastSupport.mockResolvedValueOnce({ ok: true });
      mockBackupPostMetadata.mockResolvedValueOnce({
        _yoast_wpseo_schema: '{"@context":"https://schema.org","@type":"WebPage"}',
      });
      mockBuildMetadataUpdate.mockReturnValueOnce({
        _yoast_wpseo_schema: JSON.stringify(generatedSchema),
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
