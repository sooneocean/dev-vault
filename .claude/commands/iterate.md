# /iterate — Product Iteration Automation

Automate the product iteration cycle: analyze your last release, propose next features, create issues, and publish releases.

## Usage

```
/iterate propose          # Analyze and propose next features
/iterate confirm          # Review proposals and create issues
/iterate release          # Generate changelog and create GitHub release
```

## Setup

Before running, ensure:

1. **GitHub token**: Set `GITHUB_TOKEN` env var
2. **Claude API key**: Set `ANTHROPIC_API_KEY` env var
3. **Vault initialized**: Your project should have a version tracker note

Example environment setup:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
export ANTHROPIC_API_KEY="sk-ant-your_key_here"
```

## Subcommands

### `/iterate propose`

Analyzes your last release and open issues to propose features for the next version.

**What it does:**
1. Reads current version and last release date from vault
2. Fetches last release notes from GitHub
3. Gets open feature requests
4. Calls Claude to generate 3-5 ranked proposals
5. Creates an iteration note in vault
6. Displays proposals for review

**Example output:**

```
📊 Generated 5 feature proposals for v1.2.0:

1. **Caching Layer** | Problem: Slow responses | Effort: L | Value: H | Rank: 1
2. **API Rate Limit** | Problem: Abuse risk | Effort: S | Value: M | Rank: 2
3. **Better Logging** | Problem: Hard to debug | Effort: M | Value: M | Rank: 3
4. **Admin Dashboard** | Problem: No visibility | Effort: L | Value: H | Rank: 4
5. **Batch Operations** | Problem: Efficiency | Effort: L | Value: M | Rank: 5

👉 Run `/iterate confirm` to select features and create issues
```

### `/iterate confirm`

Let you select which proposed features to build and auto-creates GitHub issues.

**What it does:**
1. Loads proposals from previous `/iterate propose` run
2. Prompts you to select features (checkboxes or numbered)
3. Creates GitHub issue for each selected feature
4. Assigns to next-version milestone
5. Updates vault iteration note with selections

**Workflow:**

```
Which features should we build? (press Space to toggle, Enter to confirm)

☑ 1. Caching Layer
☐ 2. API Rate Limit
☑ 3. Better Logging
☐ 4. Admin Dashboard
☑ 5. Batch Operations

Creating issues...
✓ Issue #125: Caching Layer (v1.2.0)
✓ Issue #126: Better Logging (v1.2.0)
✓ Issue #127: Batch Operations (v1.2.0)

👉 Merge your features, then run `/iterate release` to publish
```

### `/iterate release`

Generate changelog, create GitHub release, and update vault.

**What it does:**
1. Validates that approved features are complete (PRs merged)
2. Fetches merged PRs since last release
3. Generates changelog (categorized: Breaking/Features/Fixes)
4. Suggests next version (based on changelog)
5. Prompts for version confirmation
6. Creates GitHub release with changelog
7. Updates vault project note with new version
8. Appends release record to iteration note

**Example:**

```
📝 Generating changelog from 8 merged PRs...

## v1.2.0 (2026-03-31)

### ✨ Features
- Caching Layer ([#125](https://github.com/...))
- Better Logging ([#126](https://github.com/...))
- Batch Operations ([#127](https://github.com/...))

### 🐛 Bug Fixes
- Fix null pointer crash ([#120](https://github.com/...))

---

💡 Suggested version: 1.2.0 (Minor bump: 3 features, 1 fix)

Confirm version (1.2.0) or enter custom: _

✓ Released v1.2.0
🔗 https://github.com/your-repo/releases/tag/v1.2.0
📚 Vault iteration note updated
```

## Configuration

Configure your project in the iteration system:

**Project Name:** Set in vault project note frontmatter

```yaml
current_version: "1.0.0"
last_release_date: "2026-03-30"
```

**GitHub Details:**
- Repo: Detected from current git remote
- Owner: Detected from remote

**Feature Request Label:** Default is `feature-request` (configurable)

## Workflow Example

**Day 1: Planning Phase**
```bash
/iterate propose
# Review proposals displayed in chat
```

**Day 1: Selection Phase**
```bash
/iterate confirm
# Select features → issues created automatically
```

**Days 2-14: Development**
- Work on issues normally
- Create PRs, review, merge

**Day 15: Release**
```bash
/iterate release
# Review changelog → confirm version → release published
```

## Troubleshooting

### "GitHub token not provided"
Set `GITHUB_TOKEN`:
```bash
export GITHUB_TOKEN="your-personal-access-token"
```

### "Claude API key not provided"
Set `ANTHROPIC_API_KEY`:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Vault project note not found"
Ensure your project has an initialized version tracker note:
```
projects/your-project-version.md
```

With frontmatter:
```yaml
current_version: "1.0.0"
last_release_date: "2026-03-30"
```

### "No proposals generated"
Fallback proposals are auto-generated if Claude API fails. Check:
- ANTHROPIC_API_KEY is valid
- Rate limits not exceeded
- Prompt is appropriate for your project

## References

- **Vault System**: `.claude/lib/vault-iteration.js`
- **GitHub Integration**: `.claude/lib/github-api.js`
- **Proposal Engine**: `.claude/lib/proposal-engine.js`
- **Changelog Generator**: `.claude/lib/changelog-generator.js`
- **Version Suggester**: `.claude/lib/version-suggester.js`

## Future Enhancements

- [ ] Scheduled releases via GitHub Actions
- [ ] Custom changelog templates
- [ ] Release rollback and management
- [ ] Multi-repo support
- [ ] Integration with project milestones
- [ ] AI polish for changelog
