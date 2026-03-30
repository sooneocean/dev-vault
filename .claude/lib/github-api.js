/**
 * GitHub API Wrapper
 *
 * Provides higher-level functions for GitHub operations:
 * - Getting last release and commit history
 * - Creating releases and tags
 * - Managing issues and milestones
 * - Reading repository metadata
 */

const https = require("https");

class GitHubAPI {
  constructor(options = {}) {
    this.token = options.token || process.env.GITHUB_TOKEN;
    this.owner = options.owner;
    this.repo = options.repo;
    this.baseUrl = "api.github.com";

    if (!this.token) {
      throw new Error(
        "GitHub token not provided. Set GITHUB_TOKEN env var or pass token in options.",
      );
    }
  }

  /**
   * Make authenticated HTTP request to GitHub API
   * @private
   */
  async _request(method, path, body = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.baseUrl,
        port: 443,
        path,
        method,
        headers: {
          Authorization: `token ${this.token}`,
          "Content-Type": "application/json",
          "User-Agent": "GitHub-Iteration-Tool",
          Accept: "application/vnd.github.v3+json",
        },
      };

      const req = https.request(options, (res) => {
        let data = "";

        res.on("data", (chunk) => {
          data += chunk;
        });

        res.on("end", () => {
          try {
            const parsed = data ? JSON.parse(data) : null;

            // Handle rate limit and common errors
            if (res.statusCode === 429) {
              const retryAfter = res.headers["retry-after"] || 60;
              reject(
                new Error(`Rate limited by GitHub. Retry after ${retryAfter}s`),
              );
              return;
            }

            if (res.statusCode >= 400) {
              const message = parsed?.message || data || res.statusMessage;
              reject(
                new Error(`GitHub API error (${res.statusCode}): ${message}`),
              );
              return;
            }

            resolve(parsed);
          } catch (error) {
            reject(new Error(`Failed to parse GitHub API response: ${error}`));
          }
        });
      });

      req.on("error", reject);

      if (body) {
        req.write(JSON.stringify(body));
      }

      req.end();
    });
  }

  /**
   * Get last release for the repository
   * @returns {Promise<{tag: string, date: string, body: string}>}
   */
  async getLastRelease() {
    try {
      const release = await this._request(
        "GET",
        `/repos/${this.owner}/${this.repo}/releases/latest`,
      );

      if (!release || !release.tag_name) {
        return null;
      }

      return {
        tag: release.tag_name,
        date: release.published_at
          ? release.published_at.split("T")[0]
          : new Date().toISOString().split("T")[0],
        body: release.body || "",
        url: release.html_url,
      };
    } catch (error) {
      // "latest" endpoint returns 404 if no releases exist
      if (error.message.includes("404")) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Get closed PRs since a given date or tag
   * @param {string} sinceDate - ISO date string (YYYY-MM-DD) or git tag
   * @returns {Promise<Array>} List of PR objects with title, number, author, merged_at
   */
  async getClosedPRsSince(sinceDate) {
    const query = `repo:${this.owner}/${this.repo} is:pr is:merged merged:>${sinceDate}`;
    const response = await this._request(
      "GET",
      `/search/issues?q=${encodeURIComponent(query)}&sort=merged&order=desc&per_page=100`,
    );

    const prs = response.items || [];
    return prs.map((pr) => ({
      number: pr.number,
      title: pr.title,
      author: pr.user?.login,
      mergedAt: pr.closed_at,
      url: pr.html_url,
      body: pr.body || "",
    }));
  }

  /**
   * Create a GitHub release
   * @param {Object} params
   * @param {string} params.tagName - Git tag name (e.g., 'v1.2.3')
   * @param {string} params.name - Release name
   * @param {string} params.body - Release notes (changelog)
   * @returns {Promise<{url: string, id: number}>}
   */
  async createRelease(params) {
    const { tagName, name, body, draft = false, prerelease = false } = params;

    const response = await this._request(
      "POST",
      `/repos/${this.owner}/${this.repo}/releases`,
      {
        tag_name: tagName,
        name: name || tagName,
        body: body || "",
        draft,
        prerelease,
      },
    );

    return {
      url: response.html_url,
      id: response.id,
    };
  }

  /**
   * Create a GitHub issue
   * @param {Object} params
   * @param {string} params.title - Issue title
   * @param {string} params.body - Issue description
   * @param {Array} params.labels - Label names
   * @param {string} params.milestone - Milestone title
   * @returns {Promise<{number: number, url: string}>}
   */
  async createIssue(params) {
    const { title, body, labels = [], milestone } = params;

    const payload = {
      title,
      body: body || "",
      labels: labels || [],
    };

    if (milestone) {
      // Resolve milestone name to number if needed
      const milestones = await this._request(
        "GET",
        `/repos/${this.owner}/${this.repo}/milestones?state=open&per_page=100`,
      );

      const foundMilestone = milestones?.find(
        (m) => m.title === milestone || m.number.toString() === milestone,
      );

      if (foundMilestone) {
        payload.milestone = foundMilestone.number;
      }
    }

    const response = await this._request(
      "POST",
      `/repos/${this.owner}/${this.repo}/issues`,
      payload,
    );

    return {
      number: response.number,
      url: response.html_url,
      id: response.id,
    };
  }

  /**
   * Get open issues by label
   * @param {string} label - Label name to filter by
   * @param {number} limit - Maximum issues to return
   * @returns {Promise<Array>} List of issue objects
   */
  async getOpenIssuesByLabel(label, limit = 50) {
    const query = `repo:${this.owner}/${this.repo} is:issue is:open label:${encodeURIComponent(label)}`;
    const response = await this._request(
      "GET",
      `/search/issues?q=${encodeURIComponent(query)}&sort=updated&order=desc&per_page=${limit}`,
    );

    return (response.items || []).map((issue) => ({
      number: issue.number,
      title: issue.title,
      body: issue.body || "",
      labels: issue.labels || [],
      url: issue.html_url,
    }));
  }

  /**
   * Get milestone by name
   * @param {string} title - Milestone title
   * @returns {Promise<Object|null>} Milestone object or null if not found
   */
  async getMilestoneByName(title) {
    const response = await this._request(
      "GET",
      `/repos/${this.owner}/${this.repo}/milestones?state=open&per_page=100`,
    );

    const milestones = response || [];
    return milestones.find((m) => m.title === title) || null;
  }

  /**
   * Create a milestone
   * @param {string} title - Milestone title
   * @param {string} description - Milestone description
   * @returns {Promise<Object>} Created milestone object
   */
  async createMilestone(title, description = "") {
    const response = await this._request(
      "POST",
      `/repos/${this.owner}/${this.repo}/milestones`,
      {
        title,
        description,
      },
    );

    return {
      number: response.number,
      title: response.title,
      url: response.html_url,
    };
  }

  /**
   * Get repository metadata
   * @returns {Promise<Object>}
   */
  async getRepositoryInfo() {
    const response = await this._request(
      "GET",
      `/repos/${this.owner}/${this.repo}`,
    );

    return {
      name: response.name,
      fullName: response.full_name,
      description: response.description,
      url: response.html_url,
      language: response.language,
      defaultBranch: response.default_branch,
    };
  }
}

module.exports = GitHubAPI;
