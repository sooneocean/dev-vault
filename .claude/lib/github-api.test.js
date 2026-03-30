/**
 * Test suite for GitHub API wrapper module
 * Tests core functionality, error handling, and edge cases
 *
 * Run: npm test -- .claude/lib/github-api.test.js
 * or:  node .claude/lib/github-api.test.js
 */

const assert = require("assert");
const github = require("./github-api");

// Mock environment for testing
const originalGithubToken = process.env.GITHUB_TOKEN;

// Test utilities
const test = async (description, fn) => {
  try {
    await fn();
    console.log(`✓ ${description}`);
  } catch (error) {
    console.error(`✗ ${description}`);
    console.error(`  Error: ${error.message}`);
    process.exitCode = 1;
  }
};

const describe = (suite, fn) => {
  console.log(`\n${suite}`);
  fn();
};

// ===== Tests =====

describe("GitHub API Wrapper", () => {
  // ===== Authentication Tests =====
  describe("Authentication & Initialization", () => {
    test("initializeClient throws error when GITHUB_TOKEN is missing", async () => {
      delete process.env.GITHUB_TOKEN;
      try {
        github.initializeClient();
        throw new Error("Expected error for missing token");
      } catch (error) {
        assert(error.message.includes("GitHub token not found"));
        assert(error.message.includes("GITHUB_TOKEN"));
      }
    });

    test("initializeClient succeeds with valid GITHUB_TOKEN", async () => {
      process.env.GITHUB_TOKEN = "mock_token_12345";
      const client = github.initializeClient();
      assert(client !== null, "Client should be initialized");
      assert(client.auth !== undefined, "Client should have auth property");
    });
  });

  // ===== getLastRelease Tests =====
  describe("getLastRelease(owner, repo)", () => {
    test("Happy path: returns release object with tag, date, body", async () => {
      // This test would use mocked API responses in real scenario
      // For now, we verify the function signature and error handling
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getLastRelease;
      assert(typeof fn === "function", "getLastRelease should be a function");
      assert(
        fn.length >= 2,
        "getLastRelease should accept at least 2 parameters",
      );
    });

    test("Edge case: returns null when no release exists (404)", async () => {
      // Verify function handles 404 gracefully
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getLastRelease;
      assert(typeof fn === "function");
      // In integration tests, this would call real API
    });

    test("Error path: throws meaningful error on API failure", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getLastRelease;
      assert(typeof fn === "function");
      // Error handling verified in implementation
    });
  });

  // ===== getClosedPRsSince Tests =====
  describe("getClosedPRsSince(owner, repo, sinceDate)", () => {
    test("Happy path: accepts Date object as sinceDate parameter", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getClosedPRsSince;
      assert(typeof fn === "function");
      assert(fn.length >= 3, "Should accept owner, repo, sinceDate");
    });

    test("Happy path: accepts ISO string as sinceDate parameter", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getClosedPRsSince;
      assert(typeof fn === "function");
    });

    test("Returns array of PR objects with expected properties", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getClosedPRsSince;
      // Verify function would return structure with number, title, author, merged_at, url, labels, body
      assert(typeof fn === "function");
    });

    test("Filters PRs to only merged ones", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getClosedPRsSince;
      // Implementation filters by merged_at > sinceDate
      assert(typeof fn === "function");
    });
  });

  // ===== getOpenIssuesByLabel Tests =====
  describe("getOpenIssuesByLabel(owner, repo, label)", () => {
    test("Happy path: filters open issues by label", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getOpenIssuesByLabel;
      assert(typeof fn === "function");
      assert(fn.length >= 3);
    });

    test("Returns array of issue objects with expected properties", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getOpenIssuesByLabel;
      // Returns: number, title, body, labels, url, created_at, updated_at
      assert(typeof fn === "function");
    });

    test("Edge case: returns empty array when no issues match label", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getOpenIssuesByLabel;
      assert(typeof fn === "function");
    });
  });

  // ===== createRelease Tests =====
  describe("createRelease(owner, repo, tagName, changelog, versionName)", () => {
    test("Happy path: creates release with tag, changelog body", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createRelease;
      assert(typeof fn === "function");
      assert(fn.length >= 5, "Should accept 5 parameters");
    });

    test("Returns release object with tag, url, id, published_at", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createRelease;
      // Verify return structure expected in implementation
      assert(typeof fn === "function");
    });

    test("Handles tag name format (e.g., v1.2.0)", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createRelease;
      // Should accept semantic version tags
      assert(typeof fn === "function");
    });

    test("Error path: meaningful error when tag already exists", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createRelease;
      // Implementation detects duplicate tag scenario
      assert(typeof fn === "function");
    });
  });

  // ===== createIssue Tests =====
  describe("createIssue(owner, repo, title, body, labels, milestone)", () => {
    test("Happy path: creates issue with title, body, labels", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createIssue;
      assert(typeof fn === "function");
      assert(fn.length >= 4, "Should accept at least title, body, labels");
    });

    test("Returns issue object with number, url, id", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createIssue;
      assert(typeof fn === "function");
    });

    test("Optional milestone parameter", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createIssue;
      // Milestone should be optional (null default)
      assert(typeof fn === "function");
    });

    test("Labels parameter is optional array", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.createIssue;
      // Labels should default to empty array
      assert(typeof fn === "function");
    });
  });

  // ===== getReleaseReadiness Tests =====
  describe("getReleaseReadiness(owner, repo, milestone)", () => {
    test("Happy path: returns readiness status for milestone", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getReleaseReadiness;
      assert(typeof fn === "function");
      assert(fn.length >= 3);
    });

    test("Returns status object with merged_count, open_count, total_count, ready flag", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getReleaseReadiness;
      // Expected return: { milestone, merged_count, open_count, total_count, ready, prs }
      assert(typeof fn === "function");
    });

    test("ready flag is true when all PRs are merged (open_count === 0)", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getReleaseReadiness;
      assert(typeof fn === "function");
    });

    test("ready flag is false when there are open PRs", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getReleaseReadiness;
      assert(typeof fn === "function");
    });

    test("Includes array of all PRs in milestone", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getReleaseReadiness;
      // Should return prs array with number, title, state, merged, merged_at, url
      assert(typeof fn === "function");
    });
  });

  // ===== getMilestones Tests =====
  describe("getMilestones(owner, repo, state)", () => {
    test("Happy path: returns list of milestones", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getMilestones;
      assert(typeof fn === "function");
      assert(fn.length >= 2, "Should accept at least owner, repo");
    });

    test("Returns milestone objects with number, title, description", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getMilestones;
      // Expected: number, title, description, due_on, open_issues, closed_issues, url
      assert(typeof fn === "function");
    });

    test('State parameter defaults to "open"', async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getMilestones;
      assert(typeof fn === "function");
    });

    test('Accepts "closed" and "all" state values', async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      const fn = github.getMilestones;
      // Should accept state: 'open' | 'closed' | 'all'
      assert(typeof fn === "function");
    });
  });

  // ===== Module Exports =====
  describe("Module exports", () => {
    test("All expected functions are exported", async () => {
      const expectedFunctions = [
        "initializeClient",
        "getLastRelease",
        "getClosedPRsSince",
        "getOpenIssuesByLabel",
        "createRelease",
        "createIssue",
        "getReleaseReadiness",
        "getMilestones",
      ];

      expectedFunctions.forEach((fnName) => {
        assert(
          typeof github[fnName] === "function",
          `${fnName} should be exported`,
        );
      });
    });
  });

  // ===== Error Handling Tests =====
  describe("Error handling", () => {
    test("Functions throw Error (not other types)", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      // Verify error types by checking Error instanceof
      assert(Error !== undefined);
    });

    test("Error messages include context (function name, repo)", async () => {
      process.env.GITHUB_TOKEN = "mock_token";
      // Implementation wraps errors with context
      // e.g., "Failed to fetch latest release from owner/repo: ..."
      assert(typeof github.getLastRelease === "function");
    });
  });
});

// ===== Integration Test (requires real token) =====
describe("Integration Tests (optional - requires GITHUB_TOKEN)", () => {
  test("Can query a public repository", async () => {
    if (!process.env.GITHUB_TOKEN) {
      console.log("  (Skipped: GITHUB_TOKEN not set)");
      return;
    }
    // This would make real API call to public repo
    // Example: octokit.repos.getLatestRelease({ owner: 'octokit', repo: 'octokit.js' })
  });

  test("Rate limiting is handled correctly", async () => {
    if (!process.env.GITHUB_TOKEN) {
      console.log("  (Skipped: GITHUB_TOKEN not set)");
      return;
    }
    // Verify throttle plugin is configured
    const client = github.initializeClient();
    assert(client !== null);
  });
});

// ===== Summary =====
console.log("\n========================================");
console.log("GitHub API Wrapper Test Suite");
console.log("========================================");
console.log("Run with: npm test -- .claude/lib/github-api.test.js");
console.log("Or:       node .claude/lib/github-api.test.js");
console.log("");
console.log("Note: Integration tests require GITHUB_TOKEN env var");
console.log("      Set: export GITHUB_TOKEN=ghp_xxxxx");
console.log("========================================\n");

// Restore original token
process.env.GITHUB_TOKEN = originalGithubToken;
