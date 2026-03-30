/**
 * version-suggester.js
 *
 * Version suggestion engine for semantic versioning.
 * Analyzes changelog content (categories: breaking changes, features, fixes)
 * and suggests appropriate MAJOR.MINOR.PATCH version bump.
 */

/**
 * Parse semantic version string into components
 * @param {string} version - Version string (e.g., "1.2.3", "0.5.0", "1.0.0-alpha")
 * @returns {Object|null} Object with {major, minor, patch, prerelease} or null if invalid
 */
function parseVersion(version) {
  if (!version || typeof version !== "string") {
    return null;
  }

  // Match semantic version pattern: X.Y.Z or X.Y.Z-prerelease
  const match = version.match(/^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$/);
  if (!match) {
    return null;
  }

  return {
    major: parseInt(match[1], 10),
    minor: parseInt(match[2], 10),
    patch: parseInt(match[3], 10),
    prerelease: match[4] || null,
  };
}

/**
 * Format version object back to string
 * @param {Object} versionObj - Object with {major, minor, patch, prerelease}
 * @returns {string} Version string
 */
function formatVersion(versionObj) {
  const base = `${versionObj.major}.${versionObj.minor}.${versionObj.patch}`;
  return versionObj.prerelease ? `${base}-${versionObj.prerelease}` : base;
}

/**
 * Analyze changelog to count entries by category
 * Expected changelog format:
 * {
 *   breakingChanges: [Array of entries],
 *   features: [Array of entries],
 *   fixes: [Array of entries],
 *   other: [Array of entries]
 * }
 *
 * Or plain text changelog (will attempt to parse)
 *
 * @param {Object|string} changelog - Parsed changelog object or markdown text
 * @returns {Object} Category counts {hasBreaking, featureCount, fixCount}
 */
function analyzeChangelog(changelog) {
  const result = {
    hasBreaking: false,
    featureCount: 0,
    fixCount: 0,
    otherCount: 0,
  };

  if (!changelog) {
    return result;
  }

  // If changelog is an object (structured format)
  if (typeof changelog === "object") {
    result.hasBreaking =
      (changelog.breakingChanges && changelog.breakingChanges.length > 0) ||
      false;
    result.featureCount =
      (changelog.features && changelog.features.length) || 0;
    result.fixCount = (changelog.fixes && changelog.fixes.length) || 0;
    result.otherCount = (changelog.other && changelog.other.length) || 0;
    return result;
  }

  // If changelog is a string, attempt basic parsing
  if (typeof changelog === "string") {
    const text = changelog.toLowerCase();

    // Look for breaking changes section
    if (text.includes("breaking change") || text.includes("breaking changes")) {
      result.hasBreaking = true;
    }

    // Count feature lines (lines starting with feat: or under features section)
    const featureMatches = changelog.match(/feat[:\s]/gi) || [];
    result.featureCount = featureMatches.length;

    // Count fix lines (lines starting with fix: or under fixes/bug fixes section)
    const fixMatches = changelog.match(/fix[:\s]/gi) || [];
    result.fixCount = fixMatches.length;

    return result;
  }

  return result;
}

/**
 * Suggest next semantic version based on current version and changelog
 *
 * @param {string} currentVersion - Current version (e.g., "1.0.0")
 * @param {Object|string} changelog - Changelog object or string
 * @returns {Object} Suggestion with {version, reasoning, breakdown}
 */
function suggestVersion(currentVersion, changelog) {
  // Validate and parse current version
  const versionObj = parseVersion(currentVersion);
  if (!versionObj) {
    return {
      version: null,
      reasoning: `Invalid current version format: "${currentVersion}". Expected format: X.Y.Z (e.g., "1.0.0")`,
      breakdown: null,
      error: true,
    };
  }

  // Analyze changelog
  const analysis = analyzeChangelog(changelog);

  // Determine version bump based on changelog content
  let newVersion = { ...versionObj, prerelease: null }; // Clear prerelease
  let reason = [];

  // For 0.x.y versions (pre-1.0), apply different rules:
  // - Breaking changes → increment minor (not major)
  // - Features → increment minor
  // - Fixes → increment patch

  const isPreRelease = versionObj.major === 0;

  if (analysis.hasBreaking) {
    if (isPreRelease) {
      // 0.x.y: breaking changes increment minor
      newVersion.minor += 1;
      newVersion.patch = 0;
      reason.push("Breaking changes detected (pre-1.0: bumps minor)");
    } else {
      // 1.x.x and above: breaking changes increment major
      newVersion.major += 1;
      newVersion.minor = 0;
      newVersion.patch = 0;
      reason.push("Breaking changes detected (bumps major)");
    }
  } else if (analysis.featureCount > 0) {
    // No breaking changes, but features present → increment minor
    newVersion.minor += 1;
    newVersion.patch = 0;
    reason.push(`${analysis.featureCount} feature(s) added (bumps minor)`);
  } else if (analysis.fixCount > 0) {
    // Only fixes → increment patch
    newVersion.patch += 1;
    reason.push(`${analysis.fixCount} fix(es) (bumps patch)`);
  } else {
    // No changes detected
    // Could keep same version or bump patch
    // Default: bump patch (conservative approach)
    newVersion.patch += 1;
    reason.push("No significant changes detected (bumps patch)");
  }

  const suggestedVersionString = formatVersion(newVersion);

  // Build reasoning string
  let reasoningText = "";
  if (reason.length > 0) {
    reasoningText = reason.join(", ");
  } else {
    reasoningText = "No changes to report";
  }

  // Ensure we didn't accidentally create a pre-release
  if (newVersion.prerelease) {
    reasoningText += ` (pre-release: ${newVersion.prerelease})`;
  }

  return {
    version: suggestedVersionString,
    reasoning: reasoningText,
    breakdown: {
      current: currentVersion,
      suggested: suggestedVersionString,
      hasBreakingChanges: analysis.hasBreaking,
      featureCount: analysis.featureCount,
      fixCount: analysis.fixCount,
      otherCount: analysis.otherCount,
      isPreRelease: isPreRelease,
    },
  };
}

/**
 * Validate that suggested version is semantically greater than current
 * @param {string} currentVersion - Current version
 * @param {string} suggestedVersion - Suggested version
 * @returns {boolean} True if suggested > current
 */
function isValidVersionBump(currentVersion, suggestedVersion) {
  const current = parseVersion(currentVersion);
  const suggested = parseVersion(suggestedVersion);

  if (!current || !suggested) {
    return false;
  }

  // Compare major.minor.patch
  if (suggested.major > current.major) return true;
  if (suggested.major < current.major) return false;

  if (suggested.minor > current.minor) return true;
  if (suggested.minor < current.minor) return false;

  if (suggested.patch > current.patch) return true;
  if (suggested.patch < current.patch) return false;

  // Versions are equal
  return false;
}

// Export functions
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    parseVersion,
    formatVersion,
    analyzeChangelog,
    suggestVersion,
    isValidVersionBump,
  };
}
