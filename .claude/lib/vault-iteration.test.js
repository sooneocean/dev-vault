/**
 * Tests for Vault Iteration System
 */

const fs = require("fs");
const path = require("path");
const VaultIterationSystem = require("./vault-iteration");

// Test helpers
function createTempDir() {
  const tempDir = path.join(__dirname, "..", "..", ".test-vault");
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  return tempDir;
}

function cleanupTempDir() {
  const tempDir = path.join(__dirname, "..", "..", ".test-vault");
  if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

function createMockProjectNote(vaultRoot, notePath, version = "1.0.0") {
  const fullPath = path.join(vaultRoot, notePath);
  const dir = path.dirname(fullPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  const content = `---
title: "Test Project — Version Tracker"
type: project
tags: [version-tracking]
created: "2026-03-30"
updated: "2026-03-30"
status: active
maturity: mature
domain: project-specific
current_version: "${version}"
last_release_date: "2026-03-30"
related: []
---

# Test Project — Version Tracker

## Current Version

**Version:** ${version}

## Completed Features (Current Cycle)

- Feature A
- Feature B
`;

  fs.writeFileSync(fullPath, content, "utf-8");
}

// Run tests
console.log("Running Vault Iteration System tests...\n");

const tests = [
  {
    name: "readProjectNote reads version correctly",
    fn: () => {
      const vaultRoot = createTempDir();
      try {
        createMockProjectNote(vaultRoot, "projects/test-version.md", "1.0.0");
        const system = new VaultIterationSystem(
          vaultRoot,
          "projects/test-version.md",
        );
        const { version } = system.readProjectNote();
        return version === "1.0.0";
      } finally {
        cleanupTempDir();
      }
    },
  },
  {
    name: "readProjectNote reads last release date",
    fn: () => {
      const vaultRoot = createTempDir();
      try {
        createMockProjectNote(vaultRoot, "projects/test-version.md", "2.0.0");
        const system = new VaultIterationSystem(
          vaultRoot,
          "projects/test-version.md",
        );
        const { lastReleaseDate } = system.readProjectNote();
        return lastReleaseDate === "2026-03-30";
      } finally {
        cleanupTempDir();
      }
    },
  },
  {
    name: "createIterationNote creates valid markdown with proposals",
    fn: () => {
      const vaultRoot = createTempDir();
      try {
        createMockProjectNote(vaultRoot, "projects/test-version.md");
        const system = new VaultIterationSystem(
          vaultRoot,
          "projects/test-version.md",
        );
        const filepath = system.createIterationNote({
          version: "1.1.0",
          date: new Date("2026-03-30"),
          proposals: [
            { title: "Test", problem: "Test", effort: "M", value: "H" },
          ],
        });

        const content = fs.readFileSync(filepath, "utf-8");
        return (
          content.includes("subtype: iteration-log") &&
          content.includes("Test") &&
          fs.existsSync(filepath)
        );
      } finally {
        cleanupTempDir();
      }
    },
  },
  {
    name: "createIterationNote has correct frontmatter",
    fn: () => {
      const vaultRoot = createTempDir();
      try {
        createMockProjectNote(vaultRoot, "projects/test-version.md");
        const system = new VaultIterationSystem(
          vaultRoot,
          "projects/test-version.md",
        );
        const filepath = system.createIterationNote({
          version: "1.1.0",
          date: new Date("2026-03-30"),
          proposals: [],
        });

        const content = fs.readFileSync(filepath, "utf-8");
        return (
          content.includes("type: project") &&
          content.includes("subtype: iteration-log") &&
          content.includes('version: "1.1.0"') &&
          content.includes("maturity: growing")
        );
      } finally {
        cleanupTempDir();
      }
    },
  },
  {
    name: "createIterationNote creates iteration directory if needed",
    fn: () => {
      const vaultRoot = createTempDir();
      try {
        createMockProjectNote(vaultRoot, "projects/test-version.md");
        const system = new VaultIterationSystem(
          vaultRoot,
          "projects/test-version.md",
        );
        const iterDir = path.join(vaultRoot, "iterations");

        if (fs.existsSync(iterDir)) {
          return false;
        }

        system.createIterationNote({
          version: "1.1.0",
          date: new Date("2026-03-30"),
          proposals: [],
        });

        return fs.existsSync(iterDir);
      } finally {
        cleanupTempDir();
      }
    },
  },
  {
    name: "updateProjectNote updates version and release date",
    fn: () => {
      const vaultRoot = createTempDir();
      try {
        createMockProjectNote(vaultRoot, "projects/test-version.md", "1.0.0");
        const system = new VaultIterationSystem(
          vaultRoot,
          "projects/test-version.md",
        );

        system.updateProjectNote({
          version: "1.1.0",
          releaseDate: "2026-03-31",
          releaseUrl: "https://github.com/...",
          features: ["Feature 1", "Feature 2"],
        });

        const { version, lastReleaseDate } = system.readProjectNote();
        return version === "1.1.0" && lastReleaseDate === "2026-03-31";
      } finally {
        cleanupTempDir();
      }
    },
  },
  {
    name: "updateProjectNote updates completed features section",
    fn: () => {
      const vaultRoot = createTempDir();
      try {
        createMockProjectNote(vaultRoot, "projects/test-version.md");
        const system = new VaultIterationSystem(
          vaultRoot,
          "projects/test-version.md",
        );

        system.updateProjectNote({
          version: "1.1.0",
          releaseDate: "2026-03-31",
          releaseUrl: "https://github.com/...",
          features: ["New Feature", "Bug Fix"],
        });

        const content = fs.readFileSync(
          path.join(vaultRoot, "projects/test-version.md"),
          "utf-8",
        );

        return content.includes("New Feature") && content.includes("Bug Fix");
      } finally {
        cleanupTempDir();
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

module.exports = VaultIterationSystem;
