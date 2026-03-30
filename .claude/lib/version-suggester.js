/**
 * Version Suggestion Engine
 *
 * Suggests the next semantic version based on changelog content
 */

/**
 * Wrapper function for test compatibility
 * Adapts changelog format and returns test-expected result shape
 * @param {string} currentVersion
 * @param {Object|string} changelog - Structured or markdown changelog
 * @returns {Object} { version, reasoning, breakdown }
 */
function suggestVersion(currentVersion, changelog) {
  const suggester = new VersionSuggester();

  // Convert structured changelog to markdown string if needed
  let changelogStr = changelog;
  if (typeof changelog === "object" && changelog !== null) {
    changelogStr = formatChangelogForAnalysis(changelog);
  }

  const result = suggester.suggestVersion(currentVersion, changelogStr);

  // Extract counts from structured changelog
  let breakingCount = 0;
  let featureCount = 0;
  let fixCount = 0;

  if (typeof changelog === "object" && changelog !== null) {
    breakingCount = changelog.breakingChanges?.length || 0;
    featureCount = changelog.features?.length || 0;
    fixCount = changelog.fixes?.length || 0;
  }

  return {
    version: result.suggested,
    reasoning: result.reason,
    breakdown: {
      current: currentVersion,
      suggested: result.suggested,
      hasBreakingChanges: result.changes.breaking,
      featureCount: featureCount,
      fixCount: fixCount,
      isPreRelease: currentVersion.startsWith("0."),
    },
  };
}

/**
 * Helper: Convert structured changelog to markdown string
 * @private
 */
function formatChangelogForAnalysis(changelog) {
  let md = "";

  if (changelog.breakingChanges && changelog.breakingChanges.length > 0) {
    md += "BREAKING CHANGES\n";
    changelog.breakingChanges.forEach((item) => {
      md += `- ${item}\n`;
    });
  }

  if (changelog.features && changelog.features.length > 0) {
    md += "Features\n";
    changelog.features.forEach((item) => {
      md += `- ${item}\n`;
    });
  }

  if (changelog.fixes && changelog.fixes.length > 0) {
    md += "Bug Fixes\n";
    changelog.fixes.forEach((item) => {
      md += `- ${item}\n`;
    });
  }

  return md || "No changes";
}

class VersionSuggester {
  /**
   * Suggest next version based on changelog
   * @param {string} currentVersion - Current version (X.Y.Z)
   * @param {string} changelog - Markdown changelog
   * @returns {Object} { suggested: string, reason: string }
   */
  suggestVersion(currentVersion, changelog) {
    const [major, minor, patch] = this._parseVersion(currentVersion);

    // Analyze changelog for change types
    const hasBreaking = this._hasBreakingChanges(changelog);
    const hasFeatures = this._hasFeatures(changelog);
    const hasFixes = this._hasFixes(changelog);

    // Apply SemVer logic
    let newMajor = major;
    let newMinor = minor;
    let newPatch = patch;
    let reason = "";

    if (hasBreaking) {
      newMajor += 1;
      newMinor = 0;
      newPatch = 0;
      reason = "Major bump: breaking changes";
    } else if (hasFeatures) {
      newMinor += 1;
      newPatch = 0;
      reason = "Minor bump: new features";
    } else if (hasFixes) {
      newPatch += 1;
      reason = "Patch bump: bug fixes only";
    } else {
      // No changes detected, suggest patch bump
      newPatch += 1;
      reason = "Patch bump: minor updates";
    }

    const suggested = `${newMajor}.${newMinor}.${newPatch}`;

    return {
      suggested,
      reason,
      changes: {
        breaking: hasBreaking,
        features: hasFeatures,
        fixes: hasFixes,
      },
    };
  }

  /**
   * Parse semantic version string
   * @private
   */
  _parseVersion(version) {
    const parts = version.split(".");
    return [
      parseInt(parts[0]) || 0,
      parseInt(parts[1]) || 0,
      parseInt(parts[2]) || 0,
    ];
  }

  /**
   * Check if changelog contains breaking changes
   * @private
   */
  _hasBreakingChanges(changelog) {
    return (
      changelog.toLowerCase().includes("breaking") || changelog.includes("⚠️")
    );
  }

  /**
   * Check if changelog contains features
   * @private
   */
  _hasFeatures(changelog) {
    return (
      changelog.toLowerCase().includes("features") ||
      changelog.includes("✨") ||
      changelog.toLowerCase().includes("feat:")
    );
  }

  /**
   * Check if changelog contains fixes
   * @private
   */
  _hasFixes(changelog) {
    return (
      changelog.toLowerCase().includes("bug fixes") ||
      changelog.includes("🐛") ||
      changelog.toLowerCase().includes("fix:")
    );
  }
}

/**
 * Helper: Parse a version string into components
 * @param {string} version - Semantic version string
 * @returns {Object|null} { major, minor, patch, prerelease } or null if invalid
 */
function parseVersion(version) {
  if (!version || typeof version !== "string") {
    return null;
  }

  const match = version.match(/^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$/);
  if (!match) {
    return null;
  }

  return {
    major: parseInt(match[1]),
    minor: parseInt(match[2]),
    patch: parseInt(match[3]),
    prerelease: match[4] || null,
  };
}

/**
 * Helper: Format version components back to string
 * @param {Object} version - Version object
 * @returns {string} Formatted version string
 */
function formatVersion(version) {
  let str = `${version.major}.${version.minor}.${version.patch}`;
  if (version.prerelease) {
    str += `-${version.prerelease}`;
  }
  return str;
}

/**
 * Helper: Analyze structured changelog
 * @param {Object|string} changelog - Changelog object or string
 * @returns {Object} { hasBreaking, featureCount, fixCount }
 */
function analyzeChangelog(changelog) {
  if (!changelog) {
    return { hasBreaking: false, featureCount: 0, fixCount: 0 };
  }

  if (typeof changelog === "object") {
    return {
      hasBreaking: (changelog.breakingChanges?.length || 0) > 0,
      featureCount: changelog.features?.length || 0,
      fixCount: changelog.fixes?.length || 0,
    };
  }

  // String changelog
  const str = changelog.toLowerCase();
  return {
    hasBreaking: str.includes("breaking") || changelog.includes("⚠️"),
    featureCount: (changelog.match(/feat:/g) || []).length,
    fixCount: (changelog.match(/fix:/g) || []).length,
  };
}

/**
 * Helper: Validate version bump
 * @param {string} currentVersion
 * @param {string} newVersion
 * @returns {boolean} True if valid bump
 */
function isValidVersionBump(currentVersion, newVersion) {
  const current = parseVersion(currentVersion);
  const next = parseVersion(newVersion);

  if (!current || !next) {
    return false;
  }

  // Check if new version is greater than current
  if (next.major > current.major) return true;
  if (next.major < current.major) return false;

  if (next.minor > current.minor) return true;
  if (next.minor < current.minor) return false;

  if (next.patch > current.patch) return true;
  if (next.patch < current.patch) return false;

  // Same version
  return false;
}

// Export as CommonJS
module.exports = VersionSuggester;
module.exports.suggestVersion = suggestVersion;
module.exports.parseVersion = parseVersion;
module.exports.formatVersion = formatVersion;
module.exports.analyzeChangelog = analyzeChangelog;
module.exports.isValidVersionBump = isValidVersionBump;
