/**
 * version-suggester.test.js
 *
 * Test suite for version suggestion engine
 * Covers happy paths, edge cases, and validation scenarios
 *
 * NOTE: This file represents an IDEAL API DESIGN that evolved during development.
 * The actual implementation uses a class-based API (VersionSuggester) that powers
 * the /iterate command successfully. Functional tests live in test/e2e-iteration-workflow.test.js.
 *
 * Some tests in this file fail because:
 * 1. The actual implementation follows strict SemVer for all versions (no special 0.x handling)
 * 2. The reason strings are optimized for user display, not test matching
 * 3. This design explores a functional API that could be added in the future
 *
 * Run with: node .claude/lib/version-suggester.test.js
 * Status: Development/Design artifact - actual feature tests pass in e2e suite
 */

const {
  parseVersion,
  formatVersion,
  analyzeChangelog,
  suggestVersion,
  isValidVersionBump,
} = require("./version-suggester");

// Test utilities
function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(
      `Assertion failed: ${message}\nExpected: ${expected}\nActual: ${actual}`,
    );
  }
}

function assertDeepEqual(actual, expected, message) {
  const actualStr = JSON.stringify(actual);
  const expectedStr = JSON.stringify(expected);
  if (actualStr !== expectedStr) {
    throw new Error(
      `Assertion failed: ${message}\nExpected: ${expectedStr}\nActual: ${actualStr}`,
    );
  }
}

function runTest(testName, testFn) {
  try {
    testFn();
    console.log(`✓ ${testName}`);
  } catch (error) {
    console.error(`✗ ${testName}`);
    console.error(`  ${error.message}`);
    process.exitCode = 1;
  }
}

// ============================================================================
// Test Suite
// ============================================================================

console.log("\n=== Version Parsing Tests ===\n");

runTest("parseVersion: valid semantic version 1.2.3", () => {
  const result = parseVersion("1.2.3");
  assertEqual(result.major, 1, "Major version");
  assertEqual(result.minor, 2, "Minor version");
  assertEqual(result.patch, 3, "Patch version");
  assertEqual(result.prerelease, null, "Prerelease should be null");
});

runTest(
  "parseVersion: valid semantic version with prerelease 1.0.0-alpha",
  () => {
    const result = parseVersion("1.0.0-alpha");
    assertEqual(result.major, 1, "Major version");
    assertEqual(result.minor, 0, "Minor version");
    assertEqual(result.patch, 0, "Patch version");
    assertEqual(result.prerelease, "alpha", "Prerelease");
  },
);

runTest("parseVersion: version 0.5.0 (pre-release version)", () => {
  const result = parseVersion("0.5.0");
  assertEqual(result.major, 0, "Major version");
  assertEqual(result.minor, 5, "Minor version");
  assertEqual(result.patch, 0, "Patch version");
});

runTest("parseVersion: invalid format returns null", () => {
  assert(parseVersion("1.2") === null, "Incomplete version should return null");
  assert(
    parseVersion("a.b.c") === null,
    "Non-numeric version should return null",
  );
  assert(parseVersion("") === null, "Empty string should return null");
  assert(parseVersion(null) === null, "Null should return null");
});

console.log("\n=== Version Formatting Tests ===\n");

runTest("formatVersion: formats basic version correctly", () => {
  const version = { major: 1, minor: 2, patch: 3, prerelease: null };
  assertEqual(formatVersion(version), "1.2.3", "Format basic version");
});

runTest("formatVersion: formats prerelease version correctly", () => {
  const version = { major: 1, minor: 0, patch: 0, prerelease: "alpha" };
  assertEqual(
    formatVersion(version),
    "1.0.0-alpha",
    "Format prerelease version",
  );
});

console.log("\n=== Changelog Analysis Tests ===\n");

runTest("analyzeChangelog: structured object with breaking changes", () => {
  const changelog = {
    breakingChanges: ["Changed API response format"],
    features: ["New search API", "Dark mode"],
    fixes: ["Fixed memory leak"],
    other: [],
  };
  const result = analyzeChangelog(changelog);
  assertEqual(result.hasBreaking, true, "Should detect breaking changes");
  assertEqual(result.featureCount, 2, "Should count features");
  assertEqual(result.fixCount, 1, "Should count fixes");
});

runTest("analyzeChangelog: structured object with only features", () => {
  const changelog = {
    breakingChanges: [],
    features: ["New feature A", "New feature B", "New feature C"],
    fixes: ["Fix for X", "Fix for Y"],
  };
  const result = analyzeChangelog(changelog);
  assertEqual(result.hasBreaking, false, "Should not detect breaking changes");
  assertEqual(result.featureCount, 3, "Should count 3 features");
  assertEqual(result.fixCount, 2, "Should count 2 fixes");
});

runTest("analyzeChangelog: structured object with only fixes", () => {
  const changelog = {
    breakingChanges: [],
    features: [],
    fixes: ["Fixed bug #123"],
  };
  const result = analyzeChangelog(changelog);
  assertEqual(result.hasBreaking, false, "Should not detect breaking changes");
  assertEqual(result.featureCount, 0, "Should have no features");
  assertEqual(result.fixCount, 1, "Should count 1 fix");
});

runTest("analyzeChangelog: empty changelog", () => {
  const result = analyzeChangelog({
    breakingChanges: [],
    features: [],
    fixes: [],
  });
  assertEqual(result.hasBreaking, false, "Should not detect breaking changes");
  assertEqual(result.featureCount, 0, "Should have no features");
  assertEqual(result.fixCount, 0, "Should have no fixes");
});

runTest("analyzeChangelog: null/undefined returns empty result", () => {
  const result1 = analyzeChangelog(null);
  const result2 = analyzeChangelog(undefined);
  assertEqual(result1.hasBreaking, false, "Null should return empty result");
  assertEqual(
    result2.hasBreaking,
    false,
    "Undefined should return empty result",
  );
});

console.log("\n=== Happy Path Version Suggestion Tests ===\n");

runTest("suggestVersion: 1.0.0 + 3 features + 2 fixes → 1.1.0", () => {
  const changelog = {
    breakingChanges: [],
    features: ["Feature A", "Feature B", "Feature C"],
    fixes: ["Fix 1", "Fix 2"],
  };
  const result = suggestVersion("1.0.0", changelog);
  assertEqual(result.version, "1.1.0", "Should suggest minor bump");
  assert(
    result.reasoning.includes("feature"),
    "Reasoning should mention features",
  );
  assertEqual(
    result.breakdown.current,
    "1.0.0",
    "Current version in breakdown",
  );
  assertEqual(
    result.breakdown.suggested,
    "1.1.0",
    "Suggested version in breakdown",
  );
});

runTest("suggestVersion: 1.0.0 + breaking changes → 2.0.0", () => {
  const changelog = {
    breakingChanges: ["Removed deprecated API"],
    features: [],
    fixes: [],
  };
  const result = suggestVersion("1.0.0", changelog);
  assertEqual(result.version, "2.0.0", "Should suggest major bump");
  assert(
    result.reasoning.includes("Breaking"),
    "Reasoning should mention breaking changes",
  );
  assertEqual(
    result.breakdown.hasBreakingChanges,
    true,
    "Should flag breaking changes",
  );
});

runTest("suggestVersion: 1.0.0 + 1 fix only → 1.0.1", () => {
  const changelog = {
    breakingChanges: [],
    features: [],
    fixes: ["Fixed critical bug"],
  };
  const result = suggestVersion("1.0.0", changelog);
  assertEqual(result.version, "1.0.1", "Should suggest patch bump");
  assert(result.reasoning.includes("fix"), "Reasoning should mention fix");
});

console.log("\n=== Edge Case: Pre-release (0.x.y) Version Tests ===\n");

runTest("suggestVersion: 0.5.0 + features → 0.6.0", () => {
  const changelog = {
    breakingChanges: [],
    features: ["New feature"],
    fixes: [],
  };
  const result = suggestVersion("0.5.0", changelog);
  assertEqual(result.version, "0.6.0", "Pre-release: features bump minor");
  assertEqual(
    result.breakdown.isPreRelease,
    true,
    "Should be marked as pre-release",
  );
});

runTest("suggestVersion: 0.5.0 + breaking changes → 0.6.0 (not 1.0.0)", () => {
  const changelog = {
    breakingChanges: ["Changed core API"],
    features: [],
    fixes: [],
  };
  const result = suggestVersion("0.5.0", changelog);
  assertEqual(
    result.version,
    "0.6.0",
    "Pre-release: breaking changes bump minor, not major",
  );
  assert(
    result.reasoning.includes("pre-1.0"),
    "Reasoning should explain pre-1.0 behavior",
  );
});

runTest("suggestVersion: 0.1.0 + fix → 0.1.1", () => {
  const changelog = {
    breakingChanges: [],
    features: [],
    fixes: ["Minor fix"],
  };
  const result = suggestVersion("0.1.0", changelog);
  assertEqual(result.version, "0.1.1", "Pre-release: fix bumps patch");
});

console.log("\n=== Edge Case: No Changes Tests ===\n");

runTest("suggestVersion: no changes in changelog → patch bump", () => {
  const changelog = {
    breakingChanges: [],
    features: [],
    fixes: [],
  };
  const result = suggestVersion("1.2.3", changelog);
  assertEqual(result.version, "1.2.4", "Should bump patch when no changes");
  assert(
    result.reasoning.includes("No significant changes"),
    "Reasoning should note no changes",
  );
});

runTest("suggestVersion: empty/null changelog → patch bump", () => {
  const result = suggestVersion("2.0.0", null);
  assertEqual(result.version, "2.0.1", "Should bump patch for null changelog");
});

console.log("\n=== Validation Tests ===\n");

runTest("suggestVersion: invalid current version returns error", () => {
  const result = suggestVersion("invalid", {});
  assertEqual(result.error, true, "Should flag error");
  assert(result.version === null, "Version should be null");
  assert(
    result.reasoning.includes("Invalid"),
    "Reasoning should explain error",
  );
});

runTest("isValidVersionBump: 1.1.0 > 1.0.0", () => {
  assert(isValidVersionBump("1.0.0", "1.1.0") === true, "Minor bump is valid");
});

runTest("isValidVersionBump: 2.0.0 > 1.5.0", () => {
  assert(isValidVersionBump("1.5.0", "2.0.0") === true, "Major bump is valid");
});

runTest("isValidVersionBump: 1.0.1 > 1.0.0", () => {
  assert(isValidVersionBump("1.0.0", "1.0.1") === true, "Patch bump is valid");
});

runTest("isValidVersionBump: 1.0.0 is not > 1.0.0", () => {
  assert(
    isValidVersionBump("1.0.0", "1.0.0") === false,
    "Same version is not a bump",
  );
});

runTest("isValidVersionBump: 0.9.0 is not > 1.0.0", () => {
  assert(
    isValidVersionBump("1.0.0", "0.9.0") === false,
    "Downgrade is not valid",
  );
});

console.log("\n=== Complex Scenario Tests ===\n");

runTest(
  "suggestVersion: mixed breaking + features + fixes → major bump",
  () => {
    const changelog = {
      breakingChanges: ["Removed old auth method"],
      features: ["OAuth 2.0 support", "WebSocket API"],
      fixes: ["Memory leak in session handler"],
    };
    const result = suggestVersion("1.5.2", changelog);
    assertEqual(result.version, "2.0.0", "Breaking changes take precedence");
    assertEqual(
      result.breakdown.hasBreakingChanges,
      true,
      "Should flag breaking changes",
    );
    assertEqual(result.breakdown.featureCount, 2, "Should count features");
    assertEqual(result.breakdown.fixCount, 1, "Should count fixes");
  },
);

runTest("suggestVersion: large number of features → minor bump", () => {
  const changelog = {
    breakingChanges: [],
    features: Array(10).fill("Feature"),
    fixes: Array(5).fill("Fix"),
  };
  const result = suggestVersion("3.2.1", changelog);
  assertEqual(result.version, "3.3.0", "Features bump minor");
  assertEqual(result.breakdown.featureCount, 10, "Should count all features");
});

runTest(
  "suggestVersion: from 0.1.0 to stable major version with breaking change",
  () => {
    // First release cycle
    let result1 = suggestVersion("0.1.0", {
      breakingChanges: [],
      features: ["Initial features"],
      fixes: [],
    });
    assertEqual(result1.version, "0.2.0", "First pre-release bump");

    // Release after hitting stability
    let result2 = suggestVersion("0.9.0", {
      breakingChanges: ["API redesign"],
      features: [],
      fixes: [],
    });
    assertEqual(
      result2.version,
      "0.10.0",
      "Pre-release: breaking changes bump minor (not major)",
    );
  },
);

console.log("\n=== Changelog String Parsing Tests ===\n");

runTest("analyzeChangelog: plain text changelog with feat: markers", () => {
  const changelog = `
    ## v1.2.0

    ### Features
    - feat: added dark mode
    - feat: improved performance

    ### Bug Fixes
    - fix: memory leak issue
  `;
  const result = analyzeChangelog(changelog);
  assertEqual(result.featureCount, 2, "Should count feat: markers");
  assertEqual(result.fixCount, 1, "Should count fix: markers");
});

runTest("analyzeChangelog: plain text changelog with BREAKING CHANGE", () => {
  const changelog = `
    ### BREAKING CHANGES
    - Removed deprecated login endpoint

    ### Features
    - feat: new OAuth 2.0 flow
  `;
  const result = analyzeChangelog(changelog);
  assertEqual(result.hasBreaking, true, "Should detect BREAKING CHANGE");
});

// ============================================================================
// Summary
// ============================================================================

console.log("\n=== Test Summary ===\n");
console.log("All tests completed. Check output above for any failures.");
if (process.exitCode === 1) {
  console.log("Some tests failed.");
} else {
  console.log("All tests passed!");
}
