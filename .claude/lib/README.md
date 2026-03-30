# GitHub API Integration Layer

Stable wrapper around GitHub API (Octokit.js) for product iteration automation.

## Overview

This module provides high-level functions for:
- Reading issues, PRs, commits from GitHub
- Creating releases and tags
- Managing GitHub workflow (milestones, issue creation)

**Authentication:** Reads `GITHUB_TOKEN` environment variable (PAT or GitHub Actions token)

**Rate Limiting:** Built-in retry logic with exponential backoff (3× retries on primary limit, 0× on secondary)

## Installation

```bash
cd .claude
npm install
```

This installs:
- `@octokit/rest` (GitHub API client)
- `@octokit/plugin-throttling` (rate limit handling)

## Usage

### Import the module

```javascript
const github = require('./.claude/lib/github-api');

// Ensure GITHUB_TOKEN is set
process.env.GITHUB_TOKEN = 'ghp_xxxxx';
```

### Core Functions

#### `getLastRelease(owner, repo)`
Get the most recent release of a repository.

```javascript
const release = await github.getLastRelease('owner', 'repo');
// Returns:
// {
//   tag: 'v1.2.0',
//   name: 'Version 1.2.0',
//   date: '2026-03-30T12:00:00Z',
//   body: '## Features\n- ...',
//   url: 'https://github.com/...',
//   id: 123456
// }

// Returns null if no release exists yet
if (!release) {
  console.log('This is the first release');
}
```

#### `getClosedPRsSince(owner, repo, sinceDate)`
Get merged PRs since a given date.

```javascript
const since = new Date('2026-03-01');
// or: const since = '2026-03-01T00:00:00Z';

const prs = await github.getClosedPRsSince('owner', 'repo', since);
// Returns array of:
// {
//   number: 123,
//   title: 'feat: Add new feature',
//   author: 'username',
//   merged_at: '2026-03-30T10:00:00Z',
//   url: 'https://github.com/...',
//   labels: ['type: feature', 'priority: high'],
//   body: 'Description of the PR'
// }
```

#### `getOpenIssuesByLabel(owner, repo, label)`
Get open issues with a specific label.

```javascript
const issues = await github.getOpenIssuesByLabel('owner', 'repo', 'type: feature');
// Returns array of:
// {
//   number: 456,
//   title: 'Feature request: ...',
//   body: 'Description',
//   labels: ['type: feature'],
//   url: 'https://github.com/...',
//   created_at: '2026-03-20T00:00:00Z',
//   updated_at: '2026-03-30T00:00:00Z'
// }
```

#### `createRelease(owner, repo, tagName, changelog, versionName)`
Create a new release and tag.

```javascript
const changelog = `## v1.3.0 (2026-03-30)

### Features
- New dashboard UI (#123)
- Performance improvements (#124)

### Bug Fixes
- Fixed authentication flow (#125)
`;

const release = await github.createRelease(
  'owner',
  'repo',
  'v1.3.0',           // tag name
  changelog,          // release body (Markdown)
  'Version 1.3.0'     // version name
);
// Returns:
// {
//   tag: 'v1.3.0',
//   name: 'Version 1.3.0',
//   url: 'https://github.com/releases/tag/v1.3.0',
//   id: 789012,
//   published_at: '2026-03-30T12:00:00Z'
// }
```

#### `createIssue(owner, repo, title, body, labels, milestone)`
Create a new GitHub issue.

```javascript
const issue = await github.createIssue(
  'owner',
  'repo',
  'Build user dashboard',           // title
  'Create a dashboard for...',       // body (Markdown)
  ['type: feature', 'priority: high'], // labels (optional)
  3                                 // milestone number (optional)
);
// Returns:
// {
//   number: 789,
//   title: 'Build user dashboard',
//   url: 'https://github.com/...',
//   id: 345678,
//   created_at: '2026-03-30T12:00:00Z'
// }
```

#### `getReleaseReadiness(owner, repo, milestone)`
Check release readiness for a milestone.

```javascript
const status = await github.getReleaseReadiness('owner', 'repo', 5);
// Returns:
// {
//   milestone: 5,
//   merged_count: 8,    // PRs merged
//   open_count: 2,      // PRs still open
//   total_count: 10,
//   ready: false,       // false if open_count > 0
//   prs: [              // all PRs in milestone
//     {
//       number: 123,
//       title: 'feat: ...',
//       state: 'closed',
//       merged: true,
//       merged_at: '2026-03-30T10:00:00Z',
//       url: '...'
//     }
//   ]
// }
```

#### `getMilestones(owner, repo, state)`
Get milestones for a repository.

```javascript
const milestones = await github.getMilestones('owner', 'repo', 'open');
// state: 'open' (default), 'closed', or 'all'
//
// Returns array of:
// {
//   number: 5,
//   title: 'v1.3.0',
//   description: 'Release notes...',
//   due_on: '2026-04-15',
//   open_issues: 2,
//   closed_issues: 8,
//   url: 'https://github.com/...'
// }
```

## Authentication

### Local Development
Create a fine-grained Personal Access Token (PAT):
1. Go to https://github.com/settings/tokens?type=beta
2. Create token with scopes: `repo`, `read:org`
3. Set environment variable: `export GITHUB_TOKEN=ghp_xxxxx`

### GitHub Actions
Token is automatically available as `secrets.GITHUB_TOKEN`:
```yaml
- name: Run iteration tool
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: node .claude/commands/iterate.js
```

## Error Handling

All functions throw errors with meaningful messages. Common scenarios:

**Missing token:**
```
GitHub token not found. Please set GITHUB_TOKEN environment variable.
For local development: create a fine-grained PAT at https://github.com/settings/tokens?type=beta
For GitHub Actions: token is automatically set by the runner
```

**API error:**
```
Failed to fetch latest release from owner/repo: Request failed with status code 404
```

**Rate limited:**
```
[GitHub API] Rate limited. Retrying after 60 seconds...
```

## Rate Limiting

The module uses Octokit's built-in throttling plugin:
- **Primary rate limit (60 req/min)**: Retries up to 3× with exponential backoff
- **Secondary rate limit (abuse)**: Does NOT retry (user must wait)

Warnings are logged to console. No action needed — retries happen automatically.

## Testing

Run the test suite:
```bash
cd .claude
npm test
```

Tests cover:
- Authentication (missing token, valid token)
- All function signatures
- Error handling
- Parameter types
- Return value structures

**Note:** Integration tests require a real GitHub token and access to a repository.

## Configuration

See `.claude/config.json` for:
- Token setup instructions
- Rate limit settings
- Module paths
- API timeout settings

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `@octokit/rest` | ^20.0.0 | GitHub API client |
| `@octokit/plugin-throttling` | ^9.0.0 | Rate limit handling |

## Integration with `/iterate` Command

This module is used by `.claude/commands/iterate.md` (the slash command):

```javascript
const github = require('./.claude/lib/github-api');

// In /iterate propose
const lastRelease = await github.getLastRelease(owner, repo);
const prs = await github.getClosedPRsSince(owner, repo, lastRelease.date);

// In /iterate confirm
const issue = await github.createIssue(owner, repo, title, body, labels, milestone);

// In /iterate release
const release = await github.createRelease(owner, repo, tag, changelog, version);
```

## Troubleshooting

**"Cannot find module '@octokit/rest'"**
```bash
cd .claude && npm install
```

**"GitHub token not found"**
```bash
export GITHUB_TOKEN=ghp_xxxxx
# Verify:
echo $GITHUB_TOKEN
```

**"Rate limited: 429"**
- Wait for `Retry-After` seconds (logged to console)
- Module retries automatically up to 3 times
- If still blocked, token has hit secondary rate limit — wait 1 hour

**"Permission denied: 403"**
- Token lacks necessary scopes
- Create new PAT with `repo` and `read:org` scopes
- Or use longer-lived token for Actions

## Next Steps

- Unit 3: AI Feature Proposal Engine (uses this module)
- Unit 4: Changelog Generation (uses `getClosedPRsSince`)
- Unit 6: `/iterate` Slash Command (orchestrates all units)
