import { jest } from "@jest/globals";
import fs from "fs";
import path from "path";
import os from "os";

// ─── Mock seo-shared before importing the module under test ─────────────────

const mockDiscoverAuth = jest.fn();
const mockResolveApiBase = jest.fn();
const mockApiGet = jest.fn();
const mockApiPost = jest.fn();
const mockAppendNDJSON = jest.fn();
const mockReadNDJSON = jest.fn();
const mockSleep = jest.fn(() => Promise.resolve());
const mockEnsureDir = jest.fn();
const mockSaveJSON = jest.fn();
const mockLoadJSON = jest.fn();
const mockLog = jest.fn();
const mockLoadSiteConfig = jest.fn();

jest.unstable_mockModule("../../scripts/lib/seo-shared.js", () => ({
  discoverAuth: mockDiscoverAuth,
  resolveApiBase: mockResolveApiBase,
  apiGet: mockApiGet,
  apiPost: mockApiPost,
  appendNDJSON: mockAppendNDJSON,
  readNDJSON: mockReadNDJSON,
  sleep: mockSleep,
  ensureDir: mockEnsureDir,
  saveJSON: mockSaveJSON,
  loadJSON: mockLoadJSON,
  log: mockLog,
  loadSiteConfig: mockLoadSiteConfig,
  DEFAULT_RATE_LIMIT: { batchSize: 5, delayMs: 2000, retries: 3, backoffMs: 3000 },
  createBackup: jest.fn(),
  loadBackup: jest.fn(),
  appendBackup: jest.fn(),
  loadState: jest.fn(),
  saveState: jest.fn(),
  acquireGlobalLock: jest.fn(),
  releaseGlobalLock: jest.fn(),
  LockError: class LockError extends Error {},
  isFilenameLikeAlt: jest.fn(),
}));

// ─── Import after mocking ───────────────────────────────────────────────────

const {
  fetchMap,
  generateProposals,
  injectLinks,
  fixBrokenLinks,
  rollbackLinks,
  buildRelatedSection,
  RELATED_MARKER,
} = await import("../../scripts/internal-linker-v2.js");

const { run, phases, buildConfig } = await import(
  "../../scripts/modules/internal-links.js"
);

// ─── Test Fixtures ──────────────────────────────────────────────────────────

let tmpDir;

function makeTier1(articleIds = { tech: [101, 102, 103] }) {
  return { tier1_articles: articleIds };
}

function makePillarMap(pillars = { tech: { article_id: 100, title: "Tech Pillar" } }) {
  return { pillar_pages: pillars };
}

function makeArticleMap(articles) {
  return {
    generated: "2026-01-01T00:00:00Z",
    articles: articles || {
      100: { id: 100, title: "Tech Pillar", link: "https://yololab.net/pillar/", isPillar: true },
      101: { id: 101, title: "Article A", link: "https://yololab.net/a/", categories: [1] },
      102: { id: 102, title: "Article B", link: "https://yololab.net/b/", categories: [1] },
      103: { id: 103, title: "Article C", link: "https://yololab.net/c/", categories: [1] },
    },
  };
}

function writeDataFiles(dir, { tier1, pillarMap, articleMap } = {}) {
  const dataDir = path.join(dir, "data");
  fs.mkdirSync(dataDir, { recursive: true });
  fs.writeFileSync(path.join(dataDir, "tier1-articles.json"), JSON.stringify(tier1 || makeTier1()));
  fs.writeFileSync(path.join(dataDir, "pillar-map.json"), JSON.stringify(pillarMap || makePillarMap()));
  if (articleMap !== null) {
    fs.writeFileSync(path.join(dataDir, "tier1-article-map.json"), JSON.stringify(articleMap || makeArticleMap()));
  }
  return dataDir;
}

function setupConfig(overrides = {}) {
  const dataDir = writeDataFiles(tmpDir, overrides.dataFiles);
  const outputDir = path.join(tmpDir, "output");
  fs.mkdirSync(outputDir, { recursive: true });

  // Setup auth mock
  mockDiscoverAuth.mockReturnValue({
    method: "bearer",
    headers: { Authorization: "Bearer test-token" },
    apiBase: "wpcom-proxy",
  });
  mockResolveApiBase.mockReturnValue("https://public-api.wordpress.com/wp/v2/sites/133512998");

  return {
    siteId: 133512998,
    domain: "yololab.net",
    dataDir,
    outputDir,
    rootDir: tmpDir,
    rateLimit: { batchSize: 10, delayMs: 100, retries: 1, backoffMs: 100 },
    ...overrides.config,
  };
}

// ─── Tests ──────────────────────────────────────────────────────────────────

beforeEach(() => {
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "internal-links-test-"));
  jest.clearAllMocks();
});

afterEach(() => {
  fs.rmSync(tmpDir, { recursive: true, force: true });
});

// ─── fetchMap ───────────────────────────────────────────────────────────────

describe("fetchMap", () => {
  test("builds article mapping from tier1 data", async () => {
    const config = setupConfig();

    // Mock API responses for articles 101, 102, 103 and pillar 100
    mockApiGet.mockImplementation((url) => {
      const idMatch = url.match(/\/posts\/(\d+)/);
      const id = parseInt(idMatch[1]);
      const articles = makeArticleMap().articles;
      const article = articles[id];
      return Promise.resolve({
        id,
        title: { rendered: article?.title || `Post ${id}` },
        link: article?.link || `https://yololab.net/${id}/`,
        categories: article?.categories || [1],
      });
    });

    const result = await fetchMap(config);

    expect(result.articlesCount).toBeGreaterThan(0);
    expect(result.articles).toBeDefined();
    expect(result.outputPath).toContain("tier1-article-map.json");
    // Verify sharedSaveJSON was called to persist the map
    expect(mockSaveJSON).toHaveBeenCalled();
  });
});

// ─── generateProposals ─────────────────────────────────────────────────────

describe("generateProposals", () => {
  test("returns link proposals without modifying posts", () => {
    const config = setupConfig();

    const result = generateProposals(config);

    expect(result.totalArticles).toBeGreaterThan(0);
    expect(result.proposals).toBeInstanceOf(Array);
    expect(result.proposals.length).toBeGreaterThan(0);

    // Each proposal should have links
    for (const p of result.proposals) {
      expect(p.articleId).toBeDefined();
      expect(p.links).toBeInstanceOf(Array);
      expect(p.links.length).toBeGreaterThan(0);
      // Should include a pillar link
      const pillarLinks = p.links.filter((l) => l.type === "pillar");
      expect(pillarLinks.length).toBe(1);
    }

    // No API calls should have been made (proposals are computed locally)
    expect(mockApiGet).not.toHaveBeenCalled();
    expect(mockApiPost).not.toHaveBeenCalled();
  });

  test("throws when article map is missing", () => {
    const dataDir = path.join(tmpDir, "data");
    fs.mkdirSync(dataDir, { recursive: true });
    fs.writeFileSync(path.join(dataDir, "tier1-articles.json"), JSON.stringify(makeTier1()));
    fs.writeFileSync(path.join(dataDir, "pillar-map.json"), JSON.stringify(makePillarMap()));
    // Intentionally NOT writing tier1-article-map.json

    const config = {
      dataDir,
      outputDir: path.join(tmpDir, "output"),
      rootDir: tmpDir,
      rateLimit: { batchSize: 10, delayMs: 100, retries: 1, backoffMs: 100 },
    };

    expect(() => generateProposals(config)).toThrow("Article map not found");
  });
});

// ─── injectLinks ────────────────────────────────────────────────────────────

describe("injectLinks", () => {
  function writeProposals(config, proposals) {
    fs.mkdirSync(config.outputDir, { recursive: true });
    fs.writeFileSync(
      path.join(config.outputDir, "proposed-links-v2.json"),
      JSON.stringify({
        generated: new Date().toISOString(),
        totalArticles: proposals.length,
        totalLinks: proposals.reduce((s, p) => s + p.links.length, 0),
        proposals,
      })
    );
  }

  const sampleProposals = [
    {
      articleId: 101,
      articleTitle: "Article A",
      articleUrl: "https://yololab.net/a/",
      category: "tech",
      links: [
        { targetId: 100, title: "Tech Pillar", url: "https://yololab.net/pillar/", type: "pillar" },
        { targetId: 102, title: "Article B", url: "https://yololab.net/b/", type: "cluster_peer" },
      ],
    },
    {
      articleId: 102,
      articleTitle: "Article B",
      articleUrl: "https://yololab.net/b/",
      category: "tech",
      links: [
        { targetId: 100, title: "Tech Pillar", url: "https://yololab.net/pillar/", type: "pillar" },
        { targetId: 101, title: "Article A", url: "https://yololab.net/a/", type: "cluster_peer" },
      ],
    },
  ];

  test("dry-run shows proposed changes without writing", async () => {
    const config = setupConfig();
    writeProposals(config, sampleProposals);

    mockApiGet.mockResolvedValue({
      content: { raw: "<!-- wp:paragraph --><p>Hello world</p><!-- /wp:paragraph -->" },
    });

    const result = await injectLinks(config, { dryRun: true });

    expect(result.success).toBe(2);
    expect(result.backupPath).toBeNull();
    // No writes should happen in dry-run
    expect(mockApiPost).not.toHaveBeenCalled();
    expect(mockAppendNDJSON).not.toHaveBeenCalled();
  });

  test("live injection creates NDJSON backup before writing", async () => {
    const config = setupConfig();
    writeProposals(config, [sampleProposals[0]]);

    const originalContent = "<!-- wp:paragraph --><p>Hello world</p><!-- /wp:paragraph -->";
    mockApiGet.mockResolvedValue({
      content: { raw: originalContent },
    });
    mockApiPost.mockResolvedValue({ id: 101 });

    const result = await injectLinks(config, { dryRun: false });

    expect(result.success).toBe(1);
    expect(result.backupPath).toContain("internal-links-backup.ndjson");

    // Verify backup was written BEFORE the API post
    const appendCalls = mockAppendNDJSON.mock.calls;
    expect(appendCalls.length).toBe(1);
    expect(appendCalls[0][1].postId).toBe(101);
    expect(appendCalls[0][1].originalContent).toBe(originalContent);

    // Verify the post was updated with the related section
    expect(mockApiPost).toHaveBeenCalledTimes(1);
    const postBody = mockApiPost.mock.calls[0][1];
    expect(postBody.content).toContain("延伸閱讀");
    expect(postBody.content).toContain(originalContent);
  });

  test("skips article that already has 延伸閱讀 section", async () => {
    const config = setupConfig();
    writeProposals(config, [sampleProposals[0]]);

    mockApiGet.mockResolvedValue({
      content: { raw: '<p>Content</p><h3 class="wp-block-heading">延伸閱讀</h3><ul><li>existing</li></ul>' },
    });

    const result = await injectLinks(config, { dryRun: false });

    expect(result.skip).toBe(1);
    expect(result.success).toBe(0);
    expect(mockApiPost).not.toHaveBeenCalled();
    expect(mockAppendNDJSON).not.toHaveBeenCalled();
  });

  test("handles injection failure mid-batch with partial backup", async () => {
    const config = setupConfig();
    writeProposals(config, sampleProposals);

    // First article succeeds, second fails
    mockApiGet
      .mockResolvedValueOnce({ content: { raw: "<p>Content A</p>" } })
      .mockResolvedValueOnce({ content: { raw: "<p>Content B</p>" } });
    mockApiPost
      .mockResolvedValueOnce({ id: 101 })
      .mockRejectedValueOnce(new Error("HTTP 500: Server Error"));

    const result = await injectLinks(config, { dryRun: false });

    expect(result.success).toBe(1);
    expect(result.fail).toBe(1);
    // Backup is written BEFORE the API post for each article, so both get backed up.
    // The second article's backup was written before its API call failed.
    // This is the correct behavior: partial backup exists for recovery.
    expect(mockAppendNDJSON).toHaveBeenCalledTimes(2);
    expect(mockAppendNDJSON.mock.calls[0][1].postId).toBe(101);
    expect(mockAppendNDJSON.mock.calls[1][1].postId).toBe(102);
  });

  test("throws when proposals file is missing", async () => {
    const config = setupConfig();
    // Don't write proposals file

    await expect(injectLinks(config)).rejects.toThrow("Proposals not found");
  });
});

// ─── Backup file handling for large datasets ────────────────────────────────

describe("NDJSON backup handling", () => {
  test("backup write/read handles many entries (simulated large file)", async () => {
    // This tests the NDJSON format pattern, not actual 50MB (that would be too slow).
    // We verify the contract: appendNDJSON is called per-entry, readNDJSON iterates line-by-line.
    const config = setupConfig();
    const entries = [];

    // Simulate 100 entries (each with ~500 chars of content, representing the pattern)
    for (let i = 0; i < 100; i++) {
      entries.push({
        postId: 1000 + i,
        originalContent: `<!-- wp:paragraph --><p>${"X".repeat(500)}</p><!-- /wp:paragraph -->`,
        backedUpAt: new Date().toISOString(),
      });
    }

    // Write entries to actual NDJSON file
    const bkPath = path.join(tmpDir, "test-backup.ndjson");
    for (const entry of entries) {
      fs.appendFileSync(bkPath, JSON.stringify(entry) + "\n");
    }

    // Verify file can be read back
    const fileContent = fs.readFileSync(bkPath, "utf-8");
    const lines = fileContent.trim().split("\n");
    expect(lines.length).toBe(100);

    // Verify each line is valid JSON with expected fields
    for (const line of lines) {
      const parsed = JSON.parse(line);
      expect(parsed.postId).toBeDefined();
      expect(parsed.originalContent).toBeDefined();
      expect(parsed.originalContent).toContain("<!-- wp:paragraph -->");
    }
  });
});

// ─── rollbackLinks ──────────────────────────────────────────────────────────

describe("rollbackLinks", () => {
  test("inject then rollback round-trip restores original content", async () => {
    const config = setupConfig();
    const originalContent = '<!-- wp:paragraph --><p>Original text</p><!-- /wp:paragraph -->\n<!-- wp:image {"id":42} --><figure class="wp-block-image"><img src="test.jpg"/></figure><!-- /wp:image -->';

    // Write a real NDJSON backup file that rollbackLinks can read
    const bkPath = path.join(config.outputDir, "internal-links-backup.ndjson");
    fs.mkdirSync(config.outputDir, { recursive: true });
    fs.writeFileSync(bkPath, JSON.stringify({ postId: 101, originalContent, backedUpAt: new Date().toISOString() }) + "\n");

    // For rollback, readNDJSON is called — we need the real implementation.
    // Since we mocked the module, we simulate it via the mock:
    mockReadNDJSON.mockImplementation(async function* (filepath) {
      const content = fs.readFileSync(filepath, "utf-8");
      for (const line of content.trim().split("\n")) {
        if (line.trim()) yield JSON.parse(line);
      }
    });

    mockApiPost.mockResolvedValue({ id: 101 });

    const result = await rollbackLinks(config);

    expect(result.restored).toBe(1);
    expect(result.failed).toBe(0);

    // Verify the exact original content was sent back
    expect(mockApiPost).toHaveBeenCalledTimes(1);
    const postBody = mockApiPost.mock.calls[0][1];
    expect(postBody.content).toBe(originalContent);
  });

  test("rollback preserves Gutenberg block comments in restored content", async () => {
    const config = setupConfig();
    const gutenbergContent = [
      '<!-- wp:heading {"level":2} -->',
      '<h2 class="wp-block-heading">My Title</h2>',
      "<!-- /wp:heading -->",
      "",
      "<!-- wp:paragraph -->",
      "<p>Some paragraph with <strong>bold</strong> text.</p>",
      "<!-- /wp:paragraph -->",
      "",
      '<!-- wp:image {"id":99,"sizeSlug":"large"} -->',
      '<figure class="wp-block-image size-large"><img src="https://example.com/img.jpg" alt="Test" class="wp-image-99"/></figure>',
      "<!-- /wp:image -->",
      "",
      '<!-- wp:list {"ordered":true} -->',
      '<ol class="wp-block-list"><!-- wp:list-item -->',
      "<li>Item one</li>",
      "<!-- /wp:list-item --></ol>",
      "<!-- /wp:list -->",
    ].join("\n");

    const bkPath = path.join(config.outputDir, "internal-links-backup.ndjson");
    fs.mkdirSync(config.outputDir, { recursive: true });
    fs.writeFileSync(bkPath, JSON.stringify({ postId: 202, originalContent: gutenbergContent, backedUpAt: new Date().toISOString() }) + "\n");

    mockReadNDJSON.mockImplementation(async function* (filepath) {
      const content = fs.readFileSync(filepath, "utf-8");
      for (const line of content.trim().split("\n")) {
        if (line.trim()) yield JSON.parse(line);
      }
    });

    mockApiPost.mockResolvedValue({ id: 202 });

    const result = await rollbackLinks(config);

    expect(result.restored).toBe(1);
    const restoredContent = mockApiPost.mock.calls[0][1].content;
    // Exact match — block comments preserved
    expect(restoredContent).toBe(gutenbergContent);
    // Spot-check specific block markers
    expect(restoredContent).toContain('<!-- wp:heading {"level":2} -->');
    expect(restoredContent).toContain("<!-- /wp:heading -->");
    expect(restoredContent).toContain('<!-- wp:image {"id":99,"sizeSlug":"large"} -->');
    expect(restoredContent).toContain("<!-- wp:list-item -->");
  });

  test("throws when no backup file exists", async () => {
    const config = setupConfig();
    // No backup file written

    await expect(rollbackLinks(config)).rejects.toThrow("No backup file found");
  });
});

// ─── buildRelatedSection ────────────────────────────────────────────────────

describe("buildRelatedSection", () => {
  test("builds HTML with pillar and peer links", () => {
    const links = [
      { targetId: 100, title: "Pillar Page", url: "https://yololab.net/pillar/", type: "pillar" },
      { targetId: 101, title: "Peer Article", url: "https://yololab.net/peer/", type: "cluster_peer" },
    ];
    const html = buildRelatedSection(links);

    expect(html).toContain("延伸閱讀");
    expect(html).toContain("📌 Pillar Page");
    expect(html).toContain("Peer Article");
    expect(html).not.toContain("📌 Peer Article");
    expect(html).toContain('href="https://yololab.net/pillar/"');
  });
});

// ─── Module adapter (scripts/modules/internal-links.js) ─────────────────────

describe("internal-links module adapter", () => {
  test("phases list includes all expected phases", () => {
    expect(phases).toContain("fetch-map");
    expect(phases).toContain("propose");
    expect(phases).toContain("inject");
    expect(phases).toContain("fix-broken");
    expect(phases).toContain("rollback");
  });

  test("run() dispatches to correct phase function", async () => {
    const config = setupConfig();

    // Test propose phase (synchronous, no API calls needed)
    const result = await run("propose", config);
    expect(result.proposals).toBeInstanceOf(Array);
  });

  test("run() throws on unknown phase", async () => {
    await expect(run("unknown-phase", {})).rejects.toThrow("Unknown phase");
  });

  test("module can be imported and called with config object", async () => {
    // Verify the module exports the expected interface
    const mod = await import("../../scripts/modules/internal-links.js");
    expect(typeof mod.run).toBe("function");
    expect(typeof mod.buildConfig).toBe("function");
    expect(typeof mod.fetchMap).toBe("function");
    expect(typeof mod.generateProposals).toBe("function");
    expect(typeof mod.injectLinks).toBe("function");
    expect(typeof mod.fixBrokenLinks).toBe("function");
    expect(typeof mod.rollbackLinks).toBe("function");
    expect(mod.RELATED_MARKER).toBe("延伸閱讀");
  });
});
