import { jest } from "@jest/globals";
import fs from "fs";
import path from "path";
import os from "os";

// ─── Mock fetch globally before importing modules ───────────────────────────

const mockFetch = jest.fn();
global.fetch = mockFetch;

// ─── Mock Anthropic SDK ─────────────────────────────────────────────────────

jest.unstable_mockModule("@anthropic-ai/sdk", () => ({
  default: class Anthropic {
    constructor() {
      this.messages = {
        create: jest.fn().mockResolvedValue({
          content: [{
            type: "tool_use",
            input: {
              alt_text: "SEO optimized alt text for testing purposes in traditional Chinese",
              is_decorative: false,
            },
          }],
        }),
      };
    }
  },
}));

// ─── Import modules after mocks ─────────────────────────────────────────────

const { buildConfig, scan, featured, inline, report, rollback } =
  await import("../../scripts/modules/image-alt.js");

const {
  phaseScan,
  phaseFeatured,
  phaseInline,
  phaseReport,
  phaseRollback,
  buildDefaultConfig,
} = await import("../../scripts/image-alt-text-optimizer.js");

const { saveJSON, loadJSON, ensureDir } = await import("../../scripts/lib/seo-shared.js");

// ─── Helpers ────────────────────────────────────────────────────────────────

function makeTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "image-alt-test-"));
}

function buildTestConfig(tmpDir) {
  return {
    siteId: 133512998,
    domain: "yololab.net",
    apiBase: "https://public-api.wordpress.com/wp/v2/sites/133512998",
    apiV1: "https://public-api.wordpress.com/rest/v1.1/sites/133512998",
    auth: {
      method: "bearer",
      headers: { Authorization: "Bearer test-token" },
      apiBase: "wpcom-proxy",
    },
    outputDir: tmpDir,
    rateLimit: { batchSize: 5, delayMs: 10, retries: 1, backoffMs: 10 },
    visionModel: "claude-haiku-4-5-20251001",
    rootDir: tmpDir,
  };
}

/** Create a mock API response for fetch */
function mockJsonResponse(data, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  });
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("image-alt module", () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = makeTmpDir();
    mockFetch.mockReset();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  // ─── buildConfig ────────────────────────────────────────────────────────

  describe("buildConfig", () => {
    const originalEnv = { ...process.env };

    afterEach(() => {
      process.env = { ...originalEnv };
    });

    test("returns config with auth when WPCOM_TOKEN is set", () => {
      process.env.WPCOM_TOKEN = "test-token";
      const config = buildConfig({ rootDir: tmpDir });
      expect(config.auth).not.toBeNull();
      expect(config.auth.method).toBe("bearer");
      expect(config.apiBase).toBeTruthy();
      expect(config.siteId).toBe(133512998);
    });

    test("returns config with error when no auth available", () => {
      delete process.env.WPCOM_TOKEN;
      delete process.env.WP_BEARER_TOKEN;
      delete process.env.WP_APP_USER;
      delete process.env.WP_APP_PASS;
      delete process.env.WP_USERNAME;
      delete process.env.WP_APP_PASSWORD;
      const config = buildConfig({ rootDir: tmpDir });
      expect(config.auth).toBeNull();
      expect(config.error).toMatch(/No auth/);
    });
  });

  // ─── buildDefaultConfig ─────────────────────────────────────────────────

  describe("buildDefaultConfig", () => {
    test("returns config object with expected shape", () => {
      const config = buildDefaultConfig();
      expect(config).toHaveProperty("siteId");
      expect(config).toHaveProperty("domain");
      expect(config).toHaveProperty("outputDir");
      expect(config).toHaveProperty("rateLimit");
      expect(config.siteId).toBe(133512998);
      expect(config.domain).toBe("yololab.net");
    });
  });

  // ─── phaseScan ──────────────────────────────────────────────────────────

  describe("phaseScan", () => {
    test("happy path: returns audit report with article count and image stats (sample=10)", async () => {
      const config = buildTestConfig(tmpDir);

      // Mock: health check (posts read)
      mockFetch
        .mockImplementationOnce(() => mockJsonResponse([{ id: 1 }])) // health: posts
        .mockImplementationOnce(() => mockJsonResponse({ media: [] })) // health: media
        // page 1: 3 posts
        .mockImplementationOnce(() => mockJsonResponse([
          {
            id: 101, title: { rendered: "Article A" }, featured_media: 501,
            content: { rendered: '<img src="https://img.example.com/a.jpg" alt="good alt text here">' },
            categories: [1],
          },
          {
            id: 102, title: { rendered: "Article B" }, featured_media: 502,
            content: { rendered: '<img src="https://img.example.com/b.jpg">' },
            categories: [2],
          },
          {
            id: 103, title: { rendered: "Article C" }, featured_media: 0,
            content: { rendered: '<img src="https://img.example.com/c.jpg" alt="IMG_1234">' },
            categories: [1],
          },
        ]))
        // page 2: empty (end pagination)
        .mockImplementationOnce(() => mockJsonResponse([]))
        // media 501
        .mockImplementationOnce(() => mockJsonResponse({
          id: 501, alt_text: "", source_url: "https://img.example.com/feat-a.jpg", title: { rendered: "Feat A" },
        }))
        // media 502
        .mockImplementationOnce(() => mockJsonResponse({
          id: 502, alt_text: "Good featured alt", source_url: "https://img.example.com/feat-b.jpg", title: { rendered: "Feat B" },
        }));

      const report = await phaseScan(config, { sample: 10, skipLock: true, skipHealthCheck: false });

      expect(report).toBeDefined();
      expect(report.totalPosts).toBe(3);
      expect(report.summary.featuredMedia.total).toBe(2);
      expect(report.summary.featuredMedia.needsAlt).toBe(1); // 501 has empty alt
      expect(report.summary.inlineImages.total).toBe(3);
      // img b has no alt attr, img c has filename-like alt
      expect(report.summary.inlineImages.needsAlt).toBe(2);

      // Verify report was saved
      const savedReport = JSON.parse(
        fs.readFileSync(path.join(tmpDir, "image-audit-report.json"), "utf-8")
      );
      expect(savedReport.totalPosts).toBe(3);
    });

    test("edge case: no articles returns empty report", async () => {
      const config = buildTestConfig(tmpDir);

      mockFetch
        .mockImplementationOnce(() => mockJsonResponse([{ id: 1 }])) // health: posts
        .mockImplementationOnce(() => mockJsonResponse({ media: [] })) // health: media
        .mockImplementationOnce(() => mockJsonResponse([])); // page 1: empty

      const report = await phaseScan(config, { sample: 0, skipLock: true });

      expect(report.totalPosts).toBe(0);
      expect(report.summary.featuredMedia.total).toBe(0);
      expect(report.summary.inlineImages.total).toBe(0);
      expect(report.posts).toEqual([]);
    });

    test("error path: invalid auth returns auth error", async () => {
      const config = buildTestConfig(tmpDir);

      // Health check fails with 401
      mockFetch.mockImplementationOnce(() =>
        Promise.resolve({ ok: false, status: 401, text: () => Promise.resolve("Unauthorized") })
      );

      await expect(
        phaseScan(config, { skipLock: true, skipHealthCheck: false })
      ).rejects.toThrow(/Health check failed/);
    });
  });

  // ─── phaseFeatured ──────────────────────────────────────────────────────

  describe("phaseFeatured", () => {
    function seedAuditReport(dir) {
      const report = {
        totalPosts: 2,
        summary: { featuredMedia: { total: 2, needsAlt: 1 } },
        posts: [
          {
            id: 101, title: "Article A", categories: [1],
            featuredMedia: { mediaId: 501, url: "https://img.example.com/feat-a.jpg", currentAlt: "", needsUpdate: true },
            inlineImages: [],
          },
          {
            id: 102, title: "Article B", categories: [2],
            featuredMedia: { mediaId: 502, url: "https://img.example.com/feat-b.jpg", currentAlt: "Good alt", needsUpdate: false },
            inlineImages: [],
          },
        ],
      };
      saveJSON(path.join(dir, "image-audit-report.json"), report);
      return report;
    }

    test("happy path: dry-run returns proposed changes without writes", async () => {
      const config = buildTestConfig(tmpDir);
      seedAuditReport(tmpDir);

      // Mock: categories fetch
      mockFetch.mockImplementationOnce(() =>
        mockJsonResponse([{ id: 1, name: "Category A" }, { id: 2, name: "Category B" }])
      );
      // No more fetch calls expected in dry-run mode (no writes)

      const state = await phaseFeatured(config, {
        dryRun: true,
        sample: 0,
        skipVerification: true,
      });

      expect(state).toBeDefined();
      expect(state.stats.updated).toBe(1); // media 501 needs update
      expect(state.stats.failed).toBe(0);
      // In dry-run, no actual API writes should have been made (only categories fetch + vision)
    });

    test("edge case: resume skips already-processed articles", async () => {
      const config = buildTestConfig(tmpDir);
      seedAuditReport(tmpDir);

      // Pre-seed state with media 501 already processed
      saveJSON(path.join(tmpDir, "state_alttext_featured.json"), {
        name: "featured",
        startTime: new Date().toISOString(),
        processed: [{ mediaId: 501, newAlt: "Already done", timestamp: new Date().toISOString() }],
        failed: [],
        skipped: [],
        partial: [],
        altCache: {},
        stats: { total: 1, updated: 1, skipped: 0, failed: 0, decorative: 0 },
      });

      // Mock: categories fetch
      mockFetch.mockImplementationOnce(() =>
        mockJsonResponse([{ id: 1, name: "Category A" }])
      );

      const state = await phaseFeatured(config, {
        dryRun: true,
        resume: true,
        skipVerification: true,
      });

      // Media 501 was already processed, 502 doesn't need update
      // So nothing new to process
      expect(state.stats.updated).toBe(1); // carryover from previous state
    });

    test("integration: creates backup file before writes", async () => {
      const config = buildTestConfig(tmpDir);
      seedAuditReport(tmpDir);

      // Mock: categories
      mockFetch
        .mockImplementationOnce(() =>
          mockJsonResponse([{ id: 1, name: "Cat A" }])
        )
        // Mock: apiPost for media update
        .mockImplementationOnce(() =>
          mockJsonResponse({ id: 501, alt_text: "new alt" })
        )
        // Mock: verification GET
        .mockImplementationOnce(() =>
          mockJsonResponse({ alt_text: "SEO optimized alt text for testing purposes in traditional Chinese" })
        );

      await phaseFeatured(config, { dryRun: false, skipVerification: false });

      const backupPath = path.join(tmpDir, "alt-text-backup-featured.json");
      expect(fs.existsSync(backupPath)).toBe(true);
      const backup = JSON.parse(fs.readFileSync(backupPath, "utf-8"));
      expect(backup.items.length).toBeGreaterThanOrEqual(1);
      expect(backup.items[0]).toHaveProperty("mediaId");
      expect(backup.items[0]).toHaveProperty("originalAlt");
    });
  });

  // ─── phaseRollback ────────────────────────────────────────────────────

  describe("phaseRollback", () => {
    test("integration: restores featured from backup", async () => {
      const config = buildTestConfig(tmpDir);

      // Create backup file
      saveJSON(path.join(tmpDir, "alt-text-backup-featured.json"), {
        created: new Date().toISOString(),
        items: [
          { mediaId: 501, originalAlt: "Original alt text" },
          { mediaId: 502, originalAlt: "" },
        ],
      });

      // Mock: apiPost for restoring media (2 calls)
      mockFetch
        .mockImplementationOnce(() => mockJsonResponse({ id: 501, alt_text: "Original alt text" }))
        .mockImplementationOnce(() => mockJsonResponse({ id: 502, alt_text: "" }));

      const result = await phaseRollback(config, "featured", { skipVerification: true });

      expect(result.results).toHaveLength(1);
      expect(result.results[0].target).toBe("featured");
      expect(result.results[0].restored).toBe(2);
      expect(result.results[0].failed).toBe(0);
    });

    test("error path: missing backup returns error in results", async () => {
      const config = buildTestConfig(tmpDir);

      const result = await phaseRollback(config, "featured", { skipVerification: true });

      expect(result.results).toHaveLength(1);
      expect(result.results[0].error).toBe("backup missing");
    });

    test("rollback target validation throws on invalid target", async () => {
      const config = buildTestConfig(tmpDir);

      await expect(
        phaseRollback(config, "invalid")
      ).rejects.toThrow(/must be featured/);
    });
  });

  // ─── phaseReport ──────────────────────────────────────────────────────

  describe("phaseReport", () => {
    test("throws when no state files exist", () => {
      const config = buildTestConfig(tmpDir);

      expect(() => phaseReport(config)).toThrow(/No state files found/);
    });

    test("happy path: generates report from state files", () => {
      const config = buildTestConfig(tmpDir);

      // Seed featured state
      saveJSON(path.join(tmpDir, "state_alttext_featured.json"), {
        stats: { total: 10, updated: 8, skipped: 1, failed: 1, decorative: 1 },
        altCache: {
          "img1.jpg": { alt_text: "A good descriptive alt text for the image", is_decorative: false },
          "img2.jpg": { alt_text: "Another well-crafted descriptive alt text for SEO optimization purposes here", is_decorative: false },
          "img3.jpg": { alt_text: "", is_decorative: true },
        },
        failed: [{ mediaId: 999, error: "timeout" }],
      });

      const result = phaseReport(config);

      expect(result.markdown).toContain("YOLO LAB");
      expect(result.reportPath).toContain("alt-text-optimization-report.md");
      expect(result.stats.featured.total).toBe(10);
      expect(result.stats.featured.updated).toBe(8);
      expect(result.stats.altTextCount).toBe(2); // 2 non-decorative
      expect(result.stats.decorativeCount).toBe(1);
      expect(fs.existsSync(result.reportPath)).toBe(true);
    });
  });

  // ─── Module wrapper (scan, featured, inline, report, rollback) ────────

  describe("module wrapper functions", () => {
    const originalEnv = { ...process.env };

    afterEach(() => {
      process.env = { ...originalEnv };
    });

    test("scan returns error when no auth", async () => {
      delete process.env.WPCOM_TOKEN;
      delete process.env.WP_BEARER_TOKEN;
      delete process.env.WP_APP_USER;
      delete process.env.WP_APP_PASS;
      delete process.env.WP_USERNAME;
      delete process.env.WP_APP_PASSWORD;

      const result = await scan({ rootDir: tmpDir });

      expect(result.ok).toBe(false);
      expect(result.phase).toBe("scan");
      expect(result.error).toMatch(/No auth/);
    });

    test("report wrapper returns structured result", () => {
      process.env.WPCOM_TOKEN = "test-token";

      // Seed state for report
      const outputDir = path.join(tmpDir, "seo-optimization-output");
      ensureDir(outputDir);
      saveJSON(path.join(outputDir, "state_alttext_featured.json"), {
        stats: { total: 5, updated: 5, skipped: 0, failed: 0, decorative: 0 },
        altCache: {
          "img1.jpg": { alt_text: "Sample alt text content", is_decorative: false },
        },
        failed: [],
      });

      const result = report({ rootDir: tmpDir });

      expect(result.ok).toBe(true);
      expect(result.phase).toBe("report");
      expect(result.report).toHaveProperty("markdown");
      expect(result.report).toHaveProperty("stats");
    });
  });
});
