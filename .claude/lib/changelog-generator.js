/**
 * Changelog Generator
 *
 * Generates human-readable changelogs from merged PRs and commit messages
 * using Conventional Commits format categorization
 */

class ChangelogGenerator {
  /**
   * Generate changelog from PRs
   * @param {Object} params
   * @param {Array} params.prs - Array of PR objects with title, number, url, body
   * @param {string} params.version - Version being released
   * @returns {string} Markdown changelog
   */
  generateChangelog(params) {
    const { prs = [], version = "1.0.0" } = params;

    if (prs.length === 0) {
      return `## ${version} (${this._dateString()})\n\nNo changes recorded.\n`;
    }

    // Categorize PRs by commit message type
    const categories = {
      breaking: [],
      features: [],
      fixes: [],
      improvements: [],
      other: [],
    };

    prs.forEach((pr) => {
      const category = this._categorizeCommit(pr.title, pr.body);
      categories[category].push(pr);
    });

    // Build changelog
    let changelog = `## ${version} (${this._dateString()})\n\n`;

    if (categories.breaking.length > 0) {
      changelog += `### ⚠️ Breaking Changes\n\n`;
      categories.breaking.forEach((pr) => {
        changelog += `- ${this._formatEntry(pr)}\n`;
      });
      changelog += "\n";
    }

    if (categories.features.length > 0) {
      changelog += `### ✨ Features\n\n`;
      categories.features.forEach((pr) => {
        changelog += `- ${this._formatEntry(pr)}\n`;
      });
      changelog += "\n";
    }

    if (categories.fixes.length > 0) {
      changelog += `### 🐛 Bug Fixes\n\n`;
      categories.fixes.forEach((pr) => {
        changelog += `- ${this._formatEntry(pr)}\n`;
      });
      changelog += "\n";
    }

    if (categories.improvements.length > 0) {
      changelog += `### 🚀 Improvements\n\n`;
      categories.improvements.forEach((pr) => {
        changelog += `- ${this._formatEntry(pr)}\n`;
      });
      changelog += "\n";
    }

    if (categories.other.length > 0) {
      changelog += `### 📝 Other Changes\n\n`;
      categories.other.forEach((pr) => {
        changelog += `- ${this._formatEntry(pr)}\n`;
      });
      changelog += "\n";
    }

    return changelog.trimEnd();
  }

  /**
   * Format a single changelog entry with link
   * @private
   */
  _formatEntry(pr) {
    const url = pr.url || `#${pr.number}`;
    return `${pr.title} ([#${pr.number}](${url}))`;
  }

  /**
   * Categorize commit based on Conventional Commits
   * @private
   */
  _categorizeCommit(title, body = "") {
    const combinedText = `${title} ${body}`.toLowerCase();

    if (
      combinedText.includes("breaking change") ||
      combinedText.includes("breaking:") ||
      title.includes("!")
    ) {
      return "breaking";
    }

    if (title.toLowerCase().startsWith("feat")) {
      return "features";
    }

    if (title.toLowerCase().startsWith("fix")) {
      return "fixes";
    }

    if (
      title.toLowerCase().startsWith("perf") ||
      title.toLowerCase().startsWith("refactor")
    ) {
      return "improvements";
    }

    return "other";
  }

  /**
   * Get today's date as YYYY-MM-DD
   * @private
   */
  _dateString() {
    return new Date().toISOString().split("T")[0];
  }
}

module.exports = ChangelogGenerator;
