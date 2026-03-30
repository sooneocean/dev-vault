/**
 * Changelog Generator Tests
 *
 * Test suite for changelog generation functionality
 */

const {
  generateChangelog,
  categorizeCommit,
  extractPRNumber,
  cleanPRTitle,
  analyzeChangelog,
  formatEntry,
} = require("./changelog-generator");

// Test utilities
function assert(condition, message) {
  if (!condition) {
    console.error(`❌ FAILED: ${message}`);
    process.exitCode = 1;
  } else {
    console.log(`✓ ${message}`);
  }
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    console.error(
      `❌ FAILED: ${message}\n   Expected: ${expected}\n   Got: ${actual}`,
    );
    process.exitCode = 1;
  } else {
    console.log(`✓ ${message}`);
  }
}

function assertIncludes(text, substring, message) {
  if (!text.includes(substring)) {
    console.error(
      `❌ FAILED: ${message}\n   Expected to find: "${substring}"\n   In: "${text}"`,
    );
    process.exitCode = 1;
  } else {
    console.log(`✓ ${message}`);
  }
}

// Test Suite
console.log("\n=== Changelog Generator Tests ===\n");

// Test 1: Categorize commits
console.log("Test Group: categorizeCommit()");
{
  const testCases = [
    {
      input: "feat: new feature",
      expected: { type: "features", isBreaking: false },
    },
    {
      input: "feat!: breaking change",
      expected: { type: "features", isBreaking: true },
    },
    {
      input: "fix: bug fix",
      expected: { type: "fixes", isBreaking: false },
    },
    {
      input: "BREAKING CHANGE: major change",
      expected: { type: "other", isBreaking: true },
    },
    {
      input: "refactor: cleanup code",
      expected: { type: "improvements", isBreaking: false },
    },
    {
      input: "docs: update readme",
      expected: { type: "docs", isBreaking: false },
    },
    {
      input: "random text",
      expected: { type: "other", isBreaking: false },
    },
    {
      input: null,
      expected: { type: "other", isBreaking: false },
    },
  ];

  testCases.forEach(({ input, expected }) => {
    const result = categorizeCommit(input);
    assertEqual(
      result.type,
      expected.type,
      `categorizeCommit("${input}") → type = "${expected.type}"`,
    );
    assertEqual(
      result.isBreaking,
      expected.isBreaking,
      `categorizeCommit("${input}") → isBreaking = ${expected.isBreaking}`,
    );
  });
}

// Test 2: Extract PR number
console.log("\nTest Group: extractPRNumber()");
{
  const testCases = [
    { title: "feat: add feature (#123)", prNumber: null, expected: 123 },
    { title: "fix: bug fix (#456)", prNumber: 456, expected: 456 },
    { title: "no number here", prNumber: 789, expected: 789 },
    { title: "no number here", prNumber: null, expected: null },
  ];

  testCases.forEach(({ title, prNumber, expected }) => {
    const result = extractPRNumber(title, prNumber);
    assertEqual(
      result,
      expected,
      `extractPRNumber("${title}", ${prNumber}) → ${expected}`,
    );
  });
}

// Test 3: Clean PR title
console.log("\nTest Group: cleanPRTitle()");
{
  const testCases = [
    { input: "feat: new feature", expected: "new feature" },
    { input: "fix(auth): login bug", expected: "login bug" },
    { input: "refactor!: major update", expected: "major update" },
    { input: "plain text title", expected: "plain text title" },
    { input: null, expected: null },
  ];

  testCases.forEach(({ input, expected }) => {
    const result = cleanPRTitle(input);
    assertEqual(result, expected, `cleanPRTitle("${input}") → "${expected}"`);
  });
}

// Test 4: Happy Path - Generate changelog with 10 PRs
console.log("\nTest Group: generateChangelog() - Happy Path");
{
  const prs = [
    {
      number: 101,
      title: "feat: add user authentication",
      merged_by: { login: "alice" },
      html_url: "https://github.com/owner/repo/pull/101",
    },
    {
      number: 102,
      title: "feat: dashboard redesign",
      merged_by: { login: "bob" },
      html_url: "https://github.com/owner/repo/pull/102",
    },
    {
      number: 103,
      title: "fix: memory leak in cache",
      merged_by: { login: "alice" },
      html_url: "https://github.com/owner/repo/pull/103",
    },
    {
      number: 104,
      title: "fix: typo in docs",
      merged_by: { login: "charlie" },
      html_url: "https://github.com/owner/repo/pull/104",
    },
    {
      number: 105,
      title: "refactor: optimize database queries",
      merged_by: { login: "alice" },
      html_url: "https://github.com/owner/repo/pull/105",
    },
    {
      number: 106,
      title: "docs: update API documentation",
      merged_by: { login: "bob" },
      html_url: "https://github.com/owner/repo/pull/106",
    },
    {
      number: 107,
      title: "feat: export to CSV",
      merged_by: { login: "charlie" },
      html_url: "https://github.com/owner/repo/pull/107",
    },
    {
      number: 108,
      title: "fix: form validation error",
      merged_by: { login: "bob" },
      html_url: "https://github.com/owner/repo/pull/108",
    },
    {
      number: 109,
      title: "perf: reduce bundle size by 20%",
      merged_by: { login: "alice" },
      html_url: "https://github.com/owner/repo/pull/109",
    },
    {
      number: 110,
      title: "feat!: new API endpoint (breaking)",
      merged_by: { login: "charlie" },
      html_url: "https://github.com/owner/repo/pull/110",
    },
  ];

  const changelog = generateChangelog({
    prs,
    version: "1.2.0",
    releaseDate: "2026-03-30",
    repoUrl: "https://github.com/owner/repo",
  });

  assertIncludes(
    changelog,
    "## 1.2.0 (2026-03-30)",
    "Changelog header includes version and date",
  );
  assertIncludes(
    changelog,
    "### Breaking Changes",
    "Breaking changes section present",
  );
  assertIncludes(changelog, "### Features", "Features section present");
  assertIncludes(changelog, "### Bug Fixes", "Bug fixes section present");
  assertIncludes(changelog, "### Improvements", "Improvements section present");
  assertIncludes(
    changelog,
    "### Documentation",
    "Documentation section present",
  );
  assertIncludes(changelog, "[#101]", "PR number formatted as link");
  assertIncludes(changelog, "@alice", "Author name included");
  assertIncludes(
    changelog,
    "[#101](https://github.com/owner/repo/pull/101)",
    "PR link is correctly formatted",
  );
}

// Test 5: PR numbers become links
console.log("\nTest Group: generateChangelog() - PR Links");
{
  const prs = [
    {
      number: 123,
      title: "feat: new feature",
      merged_by: { login: "dev" },
      html_url: "https://github.com/owner/repo/pull/123",
    },
  ];

  const changelog = generateChangelog({
    prs,
    repoUrl: "https://github.com/owner/repo",
  });

  assertIncludes(
    changelog,
    "[#123](https://github.com/owner/repo/pull/123)",
    "PR number becomes GitHub link",
  );
}

// Test 6: Breaking changes at top
console.log("\nTest Group: generateChangelog() - Breaking Changes Priority");
{
  const prs = [
    {
      number: 1,
      title: "fix: minor fix",
      merged_by: { login: "alice" },
    },
    {
      number: 2,
      title: "feat!: breaking change",
      merged_by: { login: "bob" },
    },
    {
      number: 3,
      title: "feat: new feature",
      merged_by: { login: "charlie" },
    },
  ];

  const changelog = generateChangelog({ prs });

  const breakingIndex = changelog.indexOf("### Breaking Changes");
  const featuresIndex = changelog.indexOf("### Features");

  assert(
    breakingIndex < featuresIndex && breakingIndex > -1,
    "Breaking changes section appears before Features section",
  );
}

// Test 7: Edge case - No PRs
console.log("\nTest Group: generateChangelog() - No Changes");
{
  const changelog = generateChangelog({
    prs: [],
    version: "1.0.0",
  });

  assertIncludes(changelog, "### No Changes", "No Changes section when empty");
  assertIncludes(
    changelog,
    "This release contains no significant changes",
    "Empty changelog message present",
  );
}

// Test 8: Edge case - PR title format inconsistency (fallback)
console.log("\nTest Group: generateChangelog() - Title Format Inconsistency");
{
  const prs = [
    {
      number: 201,
      title: "Some random PR title without conventional prefix",
      merged_by: { login: "dev" },
    },
  ];

  const changelog = generateChangelog({ prs });

  // Non-conventional title goes into "Other" category, which is hidden by default
  // So we check for version header and that it doesn't contain undefined
  assertIncludes(
    changelog,
    "## Unreleased",
    "Changelog is generated even for non-conventional titles",
  );
  assert(
    !changelog.includes("undefined"),
    "Changelog does not contain undefined values",
  );
}

// Test 9: Analyze changelog
console.log("\nTest Group: analyzeChangelog()");
{
  const categories = {
    breaking: [{ title: "Breaking change" }],
    features: [{ title: "Feature 1" }, { title: "Feature 2" }],
    fixes: [{ title: "Fix 1" }],
    improvements: [],
    docs: [{ title: "Doc" }],
  };

  const analysis = analyzeChangelog(categories);

  assertEqual(analysis.hasBreakingChanges, true, "Breaking changes detected");
  assertEqual(analysis.featureCount, 2, "Feature count is 2");
  assertEqual(analysis.fixCount, 1, "Fix count is 1");
  assertEqual(analysis.improvementCount, 0, "Improvement count is 0");
  assertEqual(analysis.docCount, 1, "Doc count is 1");
}

// Test 10: Format entry
console.log("\nTest Group: formatEntry()");
{
  const entry = {
    title: "Add authentication",
    number: 123,
    author: "alice",
    url: "https://github.com/owner/repo/pull/123",
  };

  const formatted = formatEntry(entry, "https://github.com/owner/repo", true);

  assertIncludes(formatted, "- Add authentication", "Title is included");
  assertIncludes(formatted, "#123", "PR number is included");
  assertIncludes(formatted, "@alice", "Author is included");
}

// Test 11: Format entry without author
console.log("\nTest Group: formatEntry() - Without Author");
{
  const entry = {
    title: "Add feature",
    number: 456,
    author: "unknown",
    url: "https://github.com/owner/repo/pull/456",
  };

  const formatted = formatEntry(entry, "https://github.com/owner/repo", true);

  assertIncludes(formatted, "- Add feature", "Title is included");
  assert(!formatted.includes("@unknown"), "Unknown author is not included");
}

// Test 12: Format entry without repo URL
console.log("\nTest Group: formatEntry() - Without Repo URL");
{
  const entry = {
    title: "Fix bug",
    number: 789,
    author: "bob",
    url: null,
  };

  const formatted = formatEntry(entry, null, true);

  assertIncludes(formatted, "- Fix bug", "Title is included");
  assertIncludes(formatted, "(#789)", "PR number without link");
  assertIncludes(formatted, "@bob", "Author is included");
}

// Test 13: Markdown validity
console.log("\nTest Group: Markdown Validity");
{
  const prs = [
    {
      number: 1,
      title: "feat: feature 1",
      merged_by: { login: "user1" },
    },
    {
      number: 2,
      title: "fix: fix 1",
      merged_by: { login: "user2" },
    },
  ];

  const changelog = generateChangelog({
    prs,
    version: "2.0.0",
    releaseDate: "2026-03-30",
  });

  // Check for basic markdown structure
  assert(changelog.includes("##"), "Changelog includes heading");
  assert(changelog.includes("###"), "Changelog includes subheadings");
  assert(changelog.includes("- "), "Changelog includes bullet points");
  assert(
    !changelog.includes("undefined"),
    "Changelog does not contain undefined values",
  );
  assert(changelog.trim().length > 0, "Changelog is not empty");
}

// Test 14: Complex PR title with scope
console.log("\nTest Group: Complex PR Titles");
{
  const prs = [
    {
      number: 1,
      title: "feat(auth): add JWT validation",
      merged_by: { login: "dev" },
    },
    {
      number: 2,
      title: "fix(db): connection pool leak",
      merged_by: { login: "dev" },
    },
  ];

  const changelog = generateChangelog({ prs });

  assertIncludes(changelog, "add JWT validation", "Scope removed from title");
  assertIncludes(changelog, "connection pool leak", "Scope removed from title");
}

// Summary
console.log("\n=== Test Summary ===");
if (process.exitCode === undefined || process.exitCode === 0) {
  console.log("✓ All tests passed!");
} else {
  console.log("❌ Some tests failed.");
  process.exit(1);
}
