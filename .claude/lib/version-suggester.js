/**
 * Version Suggestion Engine
 *
 * Suggests the next semantic version based on changelog content
 */

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
      changelog.toLowerCase().includes("breaking") ||
      changelog.includes("⚠️")
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

module.exports = VersionSuggester;
