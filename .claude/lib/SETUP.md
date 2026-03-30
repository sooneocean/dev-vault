# GitHub API Integration - Setup Guide

Quick setup guide for developers implementing the GitHub API integration layer.

## What's Been Implemented

Unit 2 of the Product Iteration Automation system includes:

1. **github-api.js** — Core wrapper module with 8 functions:
   - `getLastRelease()` - Fetch latest release
   - `getClosedPRsSince()` - Get merged PRs since date
   - `getOpenIssuesByLabel()` - Fetch open feature requests
   - `createRelease()` - Create new release with tag
   - `createIssue()` - Create GitHub issue
   - `getReleaseReadiness()` - Check milestone status
   - `getMilestones()` - List milestones
   - `initializeClient()` - Setup Octokit with auth

2. **github-api.test.js** — Comprehensive test suite (50+ test cases):
   - Authentication tests
   - Function signature verification
   - Error handling validation
   - Parameter type checking
   - Return value structure tests
   - Edge case coverage

3. **Supporting files**:
   - `config.json` — Configuration for GitHub API setup
   - `package.json` — Dependencies (Octokit.js + throttling)
   - `README.md` — Full API documentation
   - `github-api-example.js` — Usage examples
   - `SETUP.md` — This file

## Installation

### Step 1: Install Dependencies

```bash
cd .claude
npm install
```

This installs:
- `@octokit/rest@^20.0.0` — GitHub API client
- `@octokit/plugin-throttling@^9.0.0` — Rate limit handling

### Step 2: Set Up GitHub Token

#### For Local Development

1. Create a fine-grained Personal Access Token:
   - Go to: https://github.com/settings/tokens?type=beta
   - Click "Generate new token"
   - Name: `claude-code-iteration`
   - Expiration: 90 days (recommended)
   - Repository access: Select your repo(s)
   - Permissions:
     - `Contents: read` (for issues, PRs, releases)
     - `Issues: read & write` (for creating issues)
     - `Pull requests: read` (for milestone tracking)

2. Set environment variable:
   ```bash
   export GITHUB_TOKEN=ghp_xxxxx  # Replace with your token

   # Verify:
   echo $GITHUB_TOKEN
   ```

#### For GitHub Actions

Token is automatically set by the runner. No configuration needed.

In workflow file:
```yaml
- name: Run iteration
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: node .claude/lib/github-api.js
```

### Step 3: Verify Installation

Run tests to verify setup:

```bash
cd .claude
npm test
```

Expected output:
```
✓ initializeClient throws error when GITHUB_TOKEN is missing
✓ initializeClient succeeds with valid GITHUB_TOKEN
✓ getLastRelease(owner, repo)
✓ ... (50+ tests)
```

## Usage

### In Node.js Code

```javascript
const github = require('./.claude/lib/github-api');

// Example: Get last release
const release = await github.getLastRelease('owner', 'repo');
console.log(`Latest: ${release.tag} (${release.date})`);

// Example: Get merged PRs
const prs = await github.getClosedPRsSince('owner', 'repo', new Date('2026-03-01'));
console.log(`Found ${prs.length} merged PRs`);

// Example: Create release
const release = await github.createRelease(
  'owner',
  'repo',
  'v1.3.0',
  '## Features\n- New feature\n',
  'Version 1.3.0'
);
console.log(`Published: ${release.url}`);
```

### In /iterate Command

The GitHub API will be used by `.claude/commands/iterate.md`:

```bash
/iterate propose    — Uses getLastRelease, getClosedPRsSince, getOpenIssuesByLabel
/iterate confirm    — Uses createIssue to auto-create issues
/iterate release    — Uses getReleaseReadiness, createRelease
```

## Configuration

Edit `.claude/config.json` to customize:

```json
{
  "github": {
    "tokenEnvVar": "GITHUB_TOKEN",
    "requiredScopes": ["repo", "read:org"]
  },
  "api": {
    "rateLimit": {
      "primaryRetries": 3,
      "secondaryRetries": 0
    },
    "timeout": 30000
  }
}
```

## Troubleshooting

### "Cannot find module @octokit/rest"

```bash
cd .claude && npm install
```

### "GitHub token not found"

```bash
export GITHUB_TOKEN=ghp_xxxxx
# Verify:
echo $GITHUB_TOKEN
```

### "Rate limited: 429"

The module handles this automatically:
- Logs: `[GitHub API] Rate limited. Retrying after X seconds...`
- Retries: Up to 3× with exponential backoff
- If still blocked: Token has hit secondary rate limit — wait 1 hour

### "Permission denied: 403"

Token lacks necessary scopes. Create new PAT with:
- `repo` (full repository access)
- `read:org` (read organization info)

### "Request failed: 404 Not Found"

- Repository doesn't exist or is private
- Token lacks access
- API endpoint is incorrect

Verify with: `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/repos/owner/repo`

## File Structure

```
.claude/
├── lib/
│   ├── github-api.js           ← Core module (8 functions)
│   ├── github-api.test.js      ← Test suite (50+ cases)
│   ├── github-api-example.js   ← Usage examples
│   ├── README.md               ← Full API documentation
│   └── SETUP.md                ← This file
├── config.json                 ← Configuration
├── package.json                ← Dependencies
└── commands/
    └── iterate.md              ← Will use this module
```

## What's Next

### Immediate (Unit 3-5)

- **Unit 3: AI Feature Proposal Engine** — Uses `getLastRelease`, `getClosedPRsSince`, `getOpenIssuesByLabel`
- **Unit 4: Changelog Generation** — Uses `getClosedPRsSince`, formats for `createRelease`
- **Unit 5: Version Suggestion Engine** — Analyzes changelog, suggests SemVer bump

### Implementation (Unit 6)

- **Unit 6: /iterate Slash Command** — Orchestrates all units:
  ```
  /iterate propose   → Uses github-api + AI engine
  /iterate confirm   → Uses createIssue
  /iterate release   → Uses getReleaseReadiness, createRelease
  ```

### Integration (Unit 7)

- **Unit 7: End-to-end Testing** — Full workflow with mocked API responses

## API Reference

Full API documentation: See `README.md`

| Function | Parameters | Returns |
|----------|-----------|---------|
| `getLastRelease` | (owner, repo) | Release object or null |
| `getClosedPRsSince` | (owner, repo, sinceDate) | PR array |
| `getOpenIssuesByLabel` | (owner, repo, label) | Issue array |
| `createRelease` | (owner, repo, tag, changelog, name) | Release object |
| `createIssue` | (owner, repo, title, body, labels, milestone) | Issue object |
| `getReleaseReadiness` | (owner, repo, milestone) | Status object |
| `getMilestones` | (owner, repo, state) | Milestone array |
| `initializeClient` | () | Octokit instance |

## Security

- **Token storage:** Never commit token to git
- **Logging:** Module does NOT log token (masked in Octokit)
- **Environment:** Use `GITHUB_TOKEN` env var, not config file
- **Scope:** Fine-grained PAT with minimal required scopes

## Testing

Unit 2 includes comprehensive test coverage:

```bash
npm test                    # Run all tests
npm run test:github-api     # Alias
node github-api.test.js     # Direct run
```

Tests verify:
- ✓ Authentication (token required, valid format)
- ✓ Function signatures (parameters, return types)
- ✓ Error handling (meaningful messages, proper types)
- ✓ Rate limiting (retry logic, exponential backoff)
- ✓ Edge cases (no releases, empty issues, first release)

## Performance Notes

- **API calls:** Octokit paginate handles pagination automatically
- **Rate limits:** 5,000 req/hour primary, adaptive secondary
- **Caching:** Not implemented (each call is fresh)
- **Timeout:** 30 seconds default (configured in config.json)

## Dependencies

| Package | Version | Rationale |
|---------|---------|-----------|
| @octokit/rest | ^20.0.0 | Official GitHub API client, modern, well-maintained |
| @octokit/plugin-throttling | ^9.0.0 | Built-in rate limit handling, automatic retries |

No other dependencies. Lightweight module for Node.js 20+.

## Integration Examples

### Example 1: Get last release info

```javascript
const github = require('./.claude/lib/github-api');

const release = await github.getLastRelease('sooneocean', 'dev-vault');
console.log(release);
// Output:
// {
//   tag: 'v1.5.0',
//   name: 'Version 1.5.0',
//   date: '2026-03-15T10:00:00Z',
//   body: '## Features\n- ...',
//   url: 'https://github.com/sooneocean/dev-vault/releases/tag/v1.5.0',
//   id: 123456789
// }
```

### Example 2: Propose next release features

```javascript
const lastRelease = await github.getLastRelease(owner, repo);
const openFeatures = await github.getOpenIssuesByLabel(owner, repo, 'type: feature');
const recentWork = await github.getClosedPRsSince(owner, repo, lastRelease.date);

console.log(`Analyzing ${openFeatures.length} feature requests...`);
console.log(`Since last release: ${recentWork.length} PRs merged`);
// Output to AI for proposal generation
```

### Example 3: Create release after approval

```javascript
const release = await github.createRelease(
  owner,
  repo,
  'v1.5.1',
  '## Bug Fixes\n- Fixed auth issue (#123)\n',
  'Version 1.5.1'
);

console.log(`Published: ${release.url}`);
// Output: https://github.com/owner/repo/releases/tag/v1.5.1
```

## Support

For issues:
1. Check GitHub API docs: https://docs.github.com/en/rest
2. Check Octokit docs: https://octokit.github.io/rest.js
3. Review error message (includes context)
4. Verify GITHUB_TOKEN env var is set

## Summary

Unit 2 is complete with:
- ✓ Stable GitHub API wrapper (8 functions)
- ✓ Comprehensive test suite (50+ cases)
- ✓ Full documentation (README.md)
- ✓ Configuration system (config.json)
- ✓ Setup guide (this file)
- ✓ Usage examples (github-api-example.js)

Ready for Unit 3 (AI Feature Proposal Engine) integration.
