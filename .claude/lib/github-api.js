/**
 * GitHub API Integration Layer
 * Wrapper around Octokit.js with higher-level functions for:
 * - Reading issues, PRs, commits
 * - Creating releases and tags
 * - Managing GitHub workflow
 *
 * Requires: GITHUB_TOKEN environment variable (PAT or Actions token)
 * Dependencies: @octokit/rest, @octokit/plugin-throttling
 */

const { Octokit } = require("@octokit/rest");
const { throttling } = require("@octokit/plugin-throttling");

// Apply throttling plugin for rate limit handling
const OctokitWithThrottling = Octokit.plugin(throttling);

/**
 * Initialize GitHub API client with rate limiting and retry logic
 * @returns {Octokit} Configured Octokit instance
 * @throws {Error} If GITHUB_TOKEN is missing
 */
function initializeClient() {
  const token = process.env.GITHUB_TOKEN;

  if (!token) {
    throw new Error(
      "GitHub token not found. Please set GITHUB_TOKEN environment variable.\n" +
        "For local development: create a fine-grained PAT at https://github.com/settings/tokens?type=beta\n" +
        "For GitHub Actions: token is automatically set by the runner",
    );
  }

  const octokit = new OctokitWithThrottling({
    auth: token,
    throttle: {
      onRateLimit: (retryAfter, options, octokit, retryCount) => {
        console.warn(
          `[GitHub API] Rate limited. Retrying after ${retryAfter} seconds...`,
        );
        if (retryCount < 3) {
          // Retry up to 3 times on primary rate limit
          return true;
        }
        return false;
      },
      onAbuseLimit: (retryAfter, options, octokit) => {
        // Does not retry on abuse limit (secondary rate limit)
        console.error(
          `[GitHub API] Abuse limit reached. Please try again after ${retryAfter} seconds`,
        );
        return false;
      },
    },
  });

  return octokit;
}

/**
 * Get the most recent release of a repository
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @returns {Object|null} Release object with tag, date, body; null if no release exists
 * @throws {Error} If API call fails
 */
async function getLastRelease(owner, repo) {
  try {
    const octokit = initializeClient();
    const response = await octokit.repos.getLatestRelease({
      owner,
      repo,
    });

    return {
      tag: response.data.tag_name,
      name: response.data.name,
      date: response.data.published_at,
      body: response.data.body,
      url: response.data.html_url,
      id: response.data.id,
    };
  } catch (error) {
    // No release exists yet (404)
    if (error.status === 404) {
      return null;
    }
    throw new Error(
      `Failed to fetch latest release from ${owner}/${repo}: ${error.message}`,
    );
  }
}

/**
 * Get closed (merged) PRs since a given date
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {Date|string} sinceDate - Only include PRs merged after this date (ISO 8601 or Date object)
 * @returns {Array} Array of PR objects with number, title, author, merged_at
 * @throws {Error} If API call fails
 */
async function getClosedPRsSince(owner, repo, sinceDate) {
  try {
    const octokit = initializeClient();
    const sinceISO =
      sinceDate instanceof Date ? sinceDate.toISOString() : sinceDate;

    const response = await octokit.paginate(
      "GET /repos/{owner}/{repo}/pulls",
      {
        owner,
        repo,
        state: "closed",
        sort: "updated",
        direction: "desc",
        per_page: 100,
      },
      (response) => {
        // Filter to only merged PRs since date
        return response.data
          .filter(
            (pr) => pr.merged_at && new Date(pr.merged_at) > new Date(sinceISO),
          )
          .map((pr) => ({
            number: pr.number,
            title: pr.title,
            author: pr.user.login,
            merged_at: pr.merged_at,
            url: pr.html_url,
            labels: pr.labels.map((l) => l.name),
            body: pr.body,
          }));
      },
    );

    // Flatten paginated results
    return response.flat();
  } catch (error) {
    throw new Error(
      `Failed to fetch closed PRs from ${owner}/${repo}: ${error.message}`,
    );
  }
}

/**
 * Get open issues with a specific label
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {string} label - Issue label to filter by
 * @returns {Array} Array of issue objects with number, title, body, labels
 * @throws {Error} If API call fails
 */
async function getOpenIssuesByLabel(owner, repo, label) {
  try {
    const octokit = initializeClient();
    const response = await octokit.paginate(
      "GET /repos/{owner}/{repo}/issues",
      {
        owner,
        repo,
        state: "open",
        labels: label,
        sort: "updated",
        direction: "desc",
        per_page: 100,
      },
      (response) => {
        return response.data.map((issue) => ({
          number: issue.number,
          title: issue.title,
          body: issue.body,
          labels: issue.labels.map((l) => l.name),
          url: issue.html_url,
          created_at: issue.created_at,
          updated_at: issue.updated_at,
        }));
      },
    );

    return response.flat();
  } catch (error) {
    throw new Error(
      `Failed to fetch issues with label '${label}' from ${owner}/${repo}: ${error.message}`,
    );
  }
}

/**
 * Create a new release and tag
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {string} tagName - Semantic version tag (e.g., "v1.2.0")
 * @param {string} changelog - Release notes (Markdown)
 * @param {string} versionName - Human-readable version name (e.g., "Version 1.2.0")
 * @returns {Object} Release object with tag, url, id
 * @throws {Error} If API call fails
 */
async function createRelease(owner, repo, tagName, changelog, versionName) {
  try {
    const octokit = initializeClient();

    // First, check if tag already exists
    let tagExists = false;
    try {
      await octokit.git.getRef({
        owner,
        repo,
        ref: `tags/${tagName}`,
      });
      tagExists = true;
    } catch (e) {
      // Tag doesn't exist yet, which is expected
      if (e.status !== 404) {
        throw e;
      }
    }

    // Create the release (this will create the tag if it doesn't exist)
    const response = await octokit.repos.createRelease({
      owner,
      repo,
      tag_name: tagName,
      name: versionName,
      body: changelog,
      draft: false,
      prerelease: false,
    });

    return {
      tag: response.data.tag_name,
      name: response.data.name,
      url: response.data.html_url,
      id: response.data.id,
      published_at: response.data.published_at,
    };
  } catch (error) {
    throw new Error(
      `Failed to create release ${tagName} on ${owner}/${repo}: ${error.message}`,
    );
  }
}

/**
 * Create a new GitHub issue
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {string} title - Issue title
 * @param {string} body - Issue description (Markdown)
 * @param {Array<string>} labels - Issue labels
 * @param {number} milestone - Milestone ID (optional)
 * @returns {Object} Issue object with number, url, id
 * @throws {Error} If API call fails
 */
async function createIssue(
  owner,
  repo,
  title,
  body,
  labels = [],
  milestone = null,
) {
  try {
    const octokit = initializeClient();
    const payload = {
      owner,
      repo,
      title,
      body,
      labels,
    };

    if (milestone !== null) {
      payload.milestone = milestone;
    }

    const response = await octokit.issues.create(payload);

    return {
      number: response.data.number,
      title: response.data.title,
      url: response.data.html_url,
      id: response.data.id,
      created_at: response.data.created_at,
    };
  } catch (error) {
    throw new Error(
      `Failed to create issue on ${owner}/${repo}: ${error.message}`,
    );
  }
}

/**
 * Get release readiness status for a milestone
 * Checks if all PRs in a milestone are merged
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {number} milestone - Milestone number
 * @returns {Object} Readiness status with merged_count, open_count, total_count, ready (boolean)
 * @throws {Error} If API call fails
 */
async function getReleaseReadiness(owner, repo, milestone) {
  try {
    const octokit = initializeClient();

    // Get all PRs in the milestone
    const response = await octokit.paginate(
      "GET /repos/{owner}/{repo}/pulls",
      {
        owner,
        repo,
        milestone,
        state: "all",
        per_page: 100,
      },
      (response) => {
        return response.data.map((pr) => ({
          number: pr.number,
          title: pr.title,
          state: pr.state, // 'open' or 'closed'
          merged: pr.merged,
          merged_at: pr.merged_at,
          url: pr.html_url,
        }));
      },
    );

    const allPRs = response.flat();
    const merged = allPRs.filter((pr) => pr.merged).length;
    const open = allPRs.filter((pr) => pr.state === "open").length;
    const total = allPRs.length;

    return {
      milestone,
      merged_count: merged,
      open_count: open,
      total_count: total,
      ready: open === 0 && total > 0,
      prs: allPRs,
    };
  } catch (error) {
    throw new Error(
      `Failed to get release readiness for milestone ${milestone} on ${owner}/${repo}: ${error.message}`,
    );
  }
}

/**
 * Get a list of milestones for a repository
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {string} state - Milestone state ('open', 'closed', or 'all')
 * @returns {Array} Array of milestone objects with number, title, description
 * @throws {Error} If API call fails
 */
async function getMilestones(owner, repo, state = "open") {
  try {
    const octokit = initializeClient();
    const response = await octokit.paginate(
      "GET /repos/{owner}/{repo}/milestones",
      {
        owner,
        repo,
        state,
        sort: "due_date",
        direction: "asc",
        per_page: 100,
      },
      (response) => {
        return response.data.map((m) => ({
          number: m.number,
          title: m.title,
          description: m.description,
          due_on: m.due_on,
          open_issues: m.open_issues,
          closed_issues: m.closed_issues,
          url: m.html_url,
        }));
      },
    );

    return response.flat();
  } catch (error) {
    throw new Error(
      `Failed to fetch milestones from ${owner}/${repo}: ${error.message}`,
    );
  }
}

module.exports = {
  initializeClient,
  getLastRelease,
  getClosedPRsSince,
  getOpenIssuesByLabel,
  createRelease,
  createIssue,
  getReleaseReadiness,
  getMilestones,
};
