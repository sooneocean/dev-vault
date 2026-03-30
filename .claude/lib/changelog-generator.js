/**
 * Changelog Generator
 *
 * Auto-generates human-readable changelogs from merged PRs and commit messages.
 * Follows Conventional Commits (https://www.conventionalcommits.org/) and SemVer.
 */

/**
 * Categorizes a commit message or PR title by Conventional Commits type
 * @param {string} message - Commit message or PR title
 * @returns {object} { type: string, isBreaking: boolean }
 */
function categorizeCommit(message) {
  if (!message) return { type: "other", isBreaking: false };

  // Check for breaking change indicator
  const isBreaking = /^[a-z]+(\(.+\))?!:|BREAKING CHANGE:/i.test(message);

  // Extract commit type
  const match = message.match(/^([a-z]+)(\(.+\))?!?:/i);
  const type = match ? match[1].toLowerCase() : null;

  // Map conventional commit types to changelog categories
  const typeMap = {
    feat: "features",
    fix: "fixes",
    docs: "docs",
    style: "style",
    refactor: "improvements",
    perf: "improvements",
    test: "tests",
    chore: "chore",
    ci: "ci",
  };

  return {
    type: typeMap[type] || "other",
    isBreaking,
  };
}

/**
 * Parses PR number from title or link
 * @param {string} title - PR title
 * @param {number} prNumber - PR number from API
 * @returns {number} PR number
 */
function extractPRNumber(title, prNumber) {
  // If prNumber is provided by GitHub API, use it
  if (prNumber) return prNumber;

  // Otherwise try to extract from title
  const match = title.match(/#(\d+)/);
  return match ? parseInt(match[1], 10) : null;
}

/**
 * Generates a Markdown changelog from merged PRs
 *
 * @param {object} options - Options object
 * @param {Array<object>} options.prs - Array of PR objects from GitHub API
 *        Each PR should have: { number, title, labels, body, merged_by, merged_at, commits: [...] }
 * @param {string} options.version - Version string (e.g., "1.2.0")
 * @param {string} options.releaseDate - Release date (YYYY-MM-DD format, defaults to today)
 * @param {string} options.repoUrl - Repository URL for creating issue links (optional)
 * @param {boolean} options.includeAuthors - Include author names in changelog (default: true)
 * @returns {string} Markdown changelog
 */
function generateChangelog(options = {}) {
  const {
    prs = [],
    version = "Unreleased",
    releaseDate = new Date().toISOString().split("T")[0],
    repoUrl = null,
    includeAuthors = true,
  } = options;

  if (!Array.isArray(prs)) {
    throw new Error("prs must be an array");
  }

  // Categorize PRs
  const categories = {
    breaking: [],
    features: [],
    fixes: [],
    improvements: [],
    docs: [],
    other: [],
  };

  prs.forEach((pr) => {
    const { type, isBreaking } = categorizeCommit(pr.title);
    const prNumber = extractPRNumber(pr.title, pr.number);

    const entry = {
      title: cleanPRTitle(pr.title),
      number: prNumber,
      author: pr.merged_by?.login || "unknown",
      url: pr.html_url || null,
    };

    if (isBreaking) {
      categories.breaking.push(entry);
    } else if (type === "features") {
      categories.features.push(entry);
    } else if (type === "fixes") {
      categories.fixes.push(entry);
    } else if (["improvements", "perf", "refactor"].includes(type)) {
      categories.improvements.push(entry);
    } else if (type === "docs") {
      categories.docs.push(entry);
    } else {
      categories.other.push(entry);
    }
  });

  // Build changelog markdown
  let changelog = `## ${version}`;

  if (version !== "Unreleased") {
    changelog += ` (${releaseDate})`;
  }

  changelog += "\n\n";

  // Breaking Changes (always first if present)
  if (categories.breaking.length > 0) {
    changelog += "### Breaking Changes\n\n";
    categories.breaking.forEach((entry) => {
      changelog += formatEntry(entry, repoUrl, includeAuthors);
    });
    changelog += "\n";
  }

  // Features
  if (categories.features.length > 0) {
    changelog += "### Features\n\n";
    categories.features.forEach((entry) => {
      changelog += formatEntry(entry, repoUrl, includeAuthors);
    });
    changelog += "\n";
  }

  // Bug Fixes
  if (categories.fixes.length > 0) {
    changelog += "### Bug Fixes\n\n";
    categories.fixes.forEach((entry) => {
      changelog += formatEntry(entry, repoUrl, includeAuthors);
    });
    changelog += "\n";
  }

  // Improvements / Performance
  if (categories.improvements.length > 0) {
    changelog += "### Improvements\n\n";
    categories.improvements.forEach((entry) => {
      changelog += formatEntry(entry, repoUrl, includeAuthors);
    });
    changelog += "\n";
  }

  // Documentation
  if (categories.docs.length > 0) {
    changelog += "### Documentation\n\n";
    categories.docs.forEach((entry) => {
      changelog += formatEntry(entry, repoUrl, includeAuthors);
    });
    changelog += "\n";
  }

  // Other (usually hidden unless user requests)
  // For MVP, we skip the "Other" section unless there are many items

  // If no changes
  if (prs.length === 0) {
    changelog += "### No Changes\n\n";
    changelog += "This release contains no significant changes.\n";
  }

  // Add footer
  changelog = changelog.trim() + "\n";

  return changelog;
}

/**
 * Formats a single changelog entry
 * @param {object} entry - Entry object { title, number, author, url }
 * @param {string} repoUrl - Repository URL
 * @param {boolean} includeAuthors - Whether to include author name
 * @returns {string} Formatted markdown bullet point
 */
function formatEntry(entry, repoUrl, includeAuthors) {
  let line = "- ";

  // Add title
  line += entry.title;

  // Add PR link
  if (entry.number && repoUrl) {
    line += ` ([#${entry.number}](${repoUrl}/pull/${entry.number}))`;
  } else if (entry.number) {
    line += ` (#${entry.number})`;
  }

  // Add author (optional)
  if (includeAuthors && entry.author && entry.author !== "unknown") {
    line += ` — @${entry.author}`;
  }

  line += "\n";

  return line;
}

/**
 * Cleans PR title by removing conventional commit prefix
 * @param {string} title - PR title
 * @returns {string} Cleaned title
 */
function cleanPRTitle(title) {
  if (!title) return title;

  // Remove conventional commit prefix (feat:, fix:, etc.)
  return title.replace(/^[a-z]+(\(.+\))?!?:\s*/i, "").trim();
}

/**
 * Parses changelog to extract categories and entry counts
 * Useful for version suggestion
 *
 * @param {object} categories - Categorized PRs { breaking, features, fixes, improvements, docs, other }
 * @returns {object} Summary { hasBreakingChanges, featureCount, fixCount, improvementCount }
 */
function analyzeChangelog(categories) {
  return {
    hasBreakingChanges: (categories.breaking || []).length > 0,
    featureCount: (categories.features || []).length,
    fixCount: (categories.fixes || []).length,
    improvementCount: (categories.improvements || []).length,
    docCount: (categories.docs || []).length,
  };
}

module.exports = {
  generateChangelog,
  categorizeCommit,
  extractPRNumber,
  cleanPRTitle,
  analyzeChangelog,
  formatEntry,
};
