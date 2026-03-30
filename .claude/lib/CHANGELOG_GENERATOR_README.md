# Changelog Generator Module

Auto-generates human-readable changelogs from merged PRs and commit messages.

**Follows:**
- [Conventional Commits](https://www.conventionalcommits.org/) — standardized commit message format
- Semantic Versioning — automated version bump suggestions

## Key Functions

### `generateChangelog(options)`

Generates a Markdown changelog from a list of PRs.

**Parameters:**
```javascript
{
  prs: Array<{
    number: number,
    title: string,
    merged_by: { login: string },
    html_url: string,
  }>,
  version: string,           // e.g., "1.2.0" (default: "Unreleased")
  releaseDate: string,       // YYYY-MM-DD format (default: today)
  repoUrl: string,          // e.g., "https://github.com/owner/repo"
  includeAuthors: boolean   // Include author names (default: true)
}
```

**Returns:** Markdown string

### Exported Functions

- `generateChangelog(options)` — Main changelog generation
- `categorizeCommit(message)` — Categorize commit by Conventional Commits type
- `extractPRNumber(title, prNumber)` — Parse PR number from title or API
- `cleanPRTitle(title)` — Remove conventional commit prefix from title
- `analyzeChangelog(categories)` — Extract counts for version suggestion
- `formatEntry(entry, repoUrl, includeAuthors)` — Format single changelog entry

## Test Coverage

Run tests:
```bash
node .claude/lib/changelog-generator.test.js
```

**Test Scenarios (all passing):**
- ✓ Commit categorization (feat, fix, docs, refactor, perf, etc.)
- ✓ PR number extraction and linking
- ✓ Breaking change detection (feat!, BREAKING CHANGE:)
- ✓ Markdown validity (no undefined values, proper structure)
- ✓ Author attribution
- ✓ PR links formatted correctly
- ✓ Breaking changes appear first
- ✓ Empty changelog handling
- ✓ Inconsistent title format handling
- ✓ Complex titles with scope (feat(auth):)

## Categories Supported

| Conventional Commit | Category | Section |
|-------------------|----------|---------|
| `feat:` | features | ### Features |
| `fix:` | fixes | ### Bug Fixes |
| `breaking:` or `!:` | breaking | ### Breaking Changes (top) |
| `refactor:`, `perf:` | improvements | ### Improvements |
| `docs:` | docs | ### Documentation |
| Other | other | (hidden in MVP) |

## Example Output

```markdown
## 1.2.0 (2026-03-30)

### Breaking Changes

- new API endpoint ([#110](https://github.com/owner/repo/pull/110)) — @charlie

### Features

- add authentication ([#101](https://github.com/owner/repo/pull/101)) — @alice
- dashboard redesign ([#102](https://github.com/owner/repo/pull/102)) — @bob

### Bug Fixes

- memory leak ([#103](https://github.com/owner/repo/pull/103)) — @alice
- validation error ([#104](https://github.com/owner/repo/pull/104)) — @bob

### Improvements

- optimize queries ([#105](https://github.com/owner/repo/pull/105)) — @alice

### Documentation

- update API docs ([#106](https://github.com/owner/repo/pull/106)) — @bob
```

## Integration with `/iterate` Workflow

1. `/iterate release` fetches merged PRs since last release tag
2. Calls `generateChangelog()` to create human-readable changelog
3. Uses `analyzeChangelog()` to suggest next version
4. Creates GitHub release with generated changelog as body
5. Updates vault with release metadata
