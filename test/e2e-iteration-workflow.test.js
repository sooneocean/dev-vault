/**
 * End-to-End Tests for Product Iteration Workflow
 * 
 * Tests the full iteration cycle with mocked GitHub API
 */

const VaultIterationSystem = require("../.claude/lib/vault-iteration");
const ChangelogGenerator = require("../.claude/lib/changelog-generator");
const VersionSuggester = require("../.claude/lib/version-suggester");
const ProposalEngine = require("../.claude/lib/proposal-engine");
const path = require("path");
const fs = require("fs");

// Test helper: create temp vault
function createTestVault() {
  const vaultRoot = path.join(__dirname, "..", "..", ".test-e2e-vault");
  if (!fs.existsSync(vaultRoot)) {
    fs.mkdirSync(vaultRoot, { recursive: true });
  }
  return vaultRoot;
}

function cleanupTestVault() {
  const vaultRoot = path.join(__dirname, "..", "..", ".test-e2e-vault");
  if (fs.existsSync(vaultRoot)) {
    fs.rmSync(vaultRoot, { recursive: true, force: true });
  }
}

console.log("Running E2E Iteration Workflow Tests...\n");

const tests = [
  {
    name: "Full iteration cycle: propose → confirm → release",
    fn: () => {
      const vaultRoot = createTestVault();
      try {
        // 1. Initialize vault project note
        const projectNotePath = "projects/test-product.md";
        const fullPath = path.join(vaultRoot, projectNotePath);
        const dir = path.dirname(fullPath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }

        const projectNote = `---
title: "Test Product — Version Tracker"
type: project
current_version: "1.0.0"
last_release_date: "2026-03-15"
---

# Test Product

## Current Version

**Version:** 1.0.0
`;
        fs.writeFileSync(fullPath, projectNote, "utf-8");

        // 2. Create vault iteration system
        const vault = new VaultIterationSystem(vaultRoot, projectNotePath);

        // Read initial state
        const initial = vault.readProjectNote();
        if (initial.version !== "1.0.0") return false;

        // 3. Create iteration note with proposals
        const proposals = [
          {
            title: "Caching Layer",
            problem: "Slow responses",
            effort: "L",
            value: "H",
          },
          {
            title: "Better Logging",
            problem: "Hard to debug",
            effort: "M",
            value: "M",
          },
        ];

        const iterationPath = vault.createIterationNote({
          version: "1.1.0",
          date: new Date("2026-03-30"),
          proposals,
        });

        if (!fs.existsSync(iterationPath)) return false;

        // 4. Generate changelog
        const changelogGen = new ChangelogGenerator();
        const prs = [
          {
            title: "feat: Add caching",
            number: 100,
            url: "https://github.com/test/test/pull/100",
          },
          {
            title: "fix: Memory leak",
            number: 101,
            url: "https://github.com/test/test/pull/101",
          },
        ];

        const changelog = changelogGen.generateChangelog({
          prs,
          version: "1.1.0",
        });

        if (!changelog.includes("1.1.0") || !changelog.includes("Features")) {
          return false;
        }

        // 5. Suggest version
        const versionSuggester = new VersionSuggester();
        const versionSuggestion = versionSuggester.suggestVersion(
          "1.0.0",
          changelog,
        );

        if (versionSuggestion.suggested !== "1.1.0") return false;

        // 6. Update vault with release
        vault.updateProjectNote({
          version: "1.1.0",
          releaseDate: "2026-03-30",
          releaseUrl: "https://github.com/test/releases/tag/v1.1.0",
          features: ["Caching Layer", "Better Logging"],
        });

        // Verify update
        const updated = vault.readProjectNote();
        if (updated.version !== "1.1.0") return false;

        return true;
      } finally {
        cleanupTestVault();
      }
    },
  },
  {
    name: "Changelog categorization works correctly",
    fn: () => {
      const gen = new ChangelogGenerator();

      const prs = [
        {
          title: "feat: New API",
          number: 1,
          url: "https://github.com/test/test/pull/1",
        },
        {
          title: "fix: Crash bug",
          number: 2,
          url: "https://github.com/test/test/pull/2",
        },
        {
          title: "BREAKING CHANGE: Auth overhaul",
          number: 3,
          url: "https://github.com/test/test/pull/3",
        },
      ];

      const changelog = gen.generateChangelog({ prs, version: "2.0.0" });

      return (
        changelog.includes("Breaking Changes") &&
        changelog.includes("Features") &&
        changelog.includes("Bug Fixes")
      );
    },
  },
  {
    name: "Version suggestion respects SemVer rules",
    fn: () => {
      const suggester = new VersionSuggester();

      // Test major (breaking)
      let changelog = "## Breaking Changes\n- API redesign";
      let suggestion = suggester.suggestVersion("1.0.0", changelog);
      if (suggestion.suggested !== "2.0.0") return false;

      // Test minor (features)
      changelog = "## Features\n- New endpoint";
      suggestion = suggester.suggestVersion("1.0.0", changelog);
      if (suggestion.suggested !== "1.1.0") return false;

      // Test patch (fixes)
      changelog = "## Bug Fixes\n- Fix typo";
      suggestion = suggester.suggestVersion("1.0.0", changelog);
      if (suggestion.suggested !== "1.0.1") return false;

      return true;
    },
  },
  {
    name: "Vault notes have correct frontmatter structure",
    fn: () => {
      const vaultRoot = createTestVault();
      try {
        const vault = new VaultIterationSystem(
          vaultRoot,
          "projects/test.md",
        );

        // Create test project note first
        const projectDir = path.join(vaultRoot, "projects");
        if (!fs.existsSync(projectDir)) {
          fs.mkdirSync(projectDir, { recursive: true });
        }

        const projectNote = `---
title: "Test"
current_version: "1.0.0"
last_release_date: "2026-03-30"
---

# Test
`;
        fs.writeFileSync(path.join(projectDir, "test.md"), projectNote, "utf-8");

        const iterationPath = vault.createIterationNote({
          version: "1.1.0",
          date: new Date("2026-03-30"),
          proposals: [
            {
              title: "Test",
              problem: "Test",
              effort: "M",
              value: "H",
            },
          ],
        });

        const content = fs.readFileSync(iterationPath, "utf-8");

        return (
          content.includes("type: project") &&
          content.includes("subtype: iteration-log") &&
          content.includes('version: "1.1.0"') &&
          content.includes("maturity: growing")
        );
      } finally {
        cleanupTestVault();
      }
    },
  },
];

let passed = 0;
let failed = 0;

tests.forEach((test) => {
  try {
    if (test.fn()) {
      console.log(`✓ ${test.name}`);
      passed++;
    } else {
      console.log(`✗ ${test.name}`);
      failed++;
    }
  } catch (error) {
    console.log(`✗ ${test.name}: ${error.message}`);
    failed++;
  }
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
