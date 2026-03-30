/**
 * Tests for GitHub API Wrapper
 * 
 * Note: These tests use mocked HTTP responses to avoid real API calls
 */

const GitHubAPI = require("./github-api");

// Mock HTTPS module
const https = require("https");
const original_request = https.request;

let mockResponses = {};
let mockError = null;

function mockHttpsRequest(method, path, responseData, statusCode = 200) {
  mockResponses[`${method} ${path}`] = {
    data: responseData,
    statusCode,
  };
}

// Override https.request for testing
https.request = function (options, callback) {
  const key = `${options.method} ${options.path}`;
  const mockData = mockResponses[key];

  if (!mockData) {
    mockData = {
      data: { message: "Not found" },
      statusCode: 404,
    };
  }

  // Simulate response
  const res = {
    statusCode: mockData.statusCode,
    headers: {},
    on: function (event, handler) {
      if (event === "data") {
        handler(JSON.stringify(mockData.data));
      } else if (event === "end") {
        handler();
      }
    },
  };

  const req = {
    write: function () {},
    end: function () {},
    on: function () {},
  };

  // Simulate async callback
  setImmediate(() => {
    callback(res);
  });

  return req;
};

// Test suite
console.log("Running GitHub API tests...\n");

const tests = [
  {
    name: "throws error if no GitHub token provided",
    fn: () => {
      delete process.env.GITHUB_TOKEN;
      try {
        new GitHubAPI({
          owner: "test",
          repo: "test",
        });
        return false;
      } catch (error) {
        return error.message.includes("GitHub token");
      }
    },
  },
  {
    name: "initializes with token from options",
    fn: () => {
      try {
        const api = new GitHubAPI({
          token: "test-token",
          owner: "test",
          repo: "test",
        });
        return api.token === "test-token";
      } catch (error) {
        return false;
      }
    },
  },
  {
    name: "initializes with token from env var",
    fn: () => {
      process.env.GITHUB_TOKEN = "env-token";
      try {
        const api = new GitHubAPI({
          owner: "test",
          repo: "test",
        });
        return api.token === "env-token";
      } catch (error) {
        return false;
      } finally {
        delete process.env.GITHUB_TOKEN;
      }
    },
  },
  {
    name: "stores owner and repo",
    fn: () => {
      const api = new GitHubAPI({
        token: "test-token",
        owner: "octocat",
        repo: "Hello-World",
      });
      return api.owner === "octocat" && api.repo === "Hello-World";
    },
  },
  {
    name: "has method getLastRelease",
    fn: () => {
      const api = new GitHubAPI({
        token: "test-token",
        owner: "test",
        repo: "test",
      });
      return typeof api.getLastRelease === "function";
    },
  },
  {
    name: "has method getClosedPRsSince",
    fn: () => {
      const api = new GitHubAPI({
        token: "test-token",
        owner: "test",
        repo: "test",
      });
      return typeof api.getClosedPRsSince === "function";
    },
  },
  {
    name: "has method createRelease",
    fn: () => {
      const api = new GitHubAPI({
        token: "test-token",
        owner: "test",
        repo: "test",
      });
      return typeof api.createRelease === "function";
    },
  },
  {
    name: "has method createIssue",
    fn: () => {
      const api = new GitHubAPI({
        token: "test-token",
        owner: "test",
        repo: "test",
      });
      return typeof api.createIssue === "function";
    },
  },
  {
    name: "has method getRepositoryInfo",
    fn: () => {
      const api = new GitHubAPI({
        token: "test-token",
        owner: "test",
        repo: "test",
      });
      return typeof api.getRepositoryInfo === "function";
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

// Cleanup
https.request = original_request;

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);

module.exports = GitHubAPI;
