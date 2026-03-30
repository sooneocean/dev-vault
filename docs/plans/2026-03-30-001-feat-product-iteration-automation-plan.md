---
title: "feat: Product Iteration Automation Workflow"
type: feat
status: active
date: 2026-03-30
origin: docs/brainstorms/2026-03-30-product-iteration-automation-requirements.md
---

# Product Iteration Automation Workflow

## Overview

Build a Claude skill and supporting infrastructure to automate the product iteration cycle: from analyzing the last release to proposing next-version features, confirming selections, auto-creating GitHub issues, and finally publishing a GitHub release with auto-generated changelog.

**Core flow:** `/iterate propose` → review proposals → `/iterate confirm` → auto-create issues → `/iterate release` → GitHub release + vault history note

## Problem Frame

Individual developers manually manage product releases: brainstorming next features, tracking what was done, writing changelogs, creating releases. No systematic loop exists between "what shipped" and "what's next." This breaks focus and leaves value on the table.

(See origin: `docs/brainstorms/2026-03-30-product-iteration-automation-requirements.md`)

## Requirements Trace

- **R1. Version state tracking** — Vault note maintains current version, last release date, completed features since last release
- **R2. Auto-generate changelog** — From completed PRs/features, generate human-readable changelog (categories: features, fixes, breaking changes)
- **R3. GitHub release automation** — Create release with auto-generated changelog, semantic version tag, release notes
- **R4. Rollback support** — Ability to undo a release (delete tag/release on GitHub, revert version in vault)
- **R5. AI-powered feature proposal** — Analyze last release + open issues + closed PRs + vault learnings → generate 3–5 prioritized proposals
- **R6. Feature proposal presentation** — Each proposal includes title, problem, effort estimate, value estimate, prioritization
- **R7. Manual feature confirmation** — Developer approves/rejects/ranks features, tool auto-creates GitHub issues
- **R8. Feature progress tracking** — Tool tracks in-progress features (PRs), completed features (since last release), remaining work
- **R9. Release readiness check** — Indicate: features complete? Tests passing? Blocking issues?
- **R10. Scheduled/on-demand triggering** — On-demand `/iterate` command, optional GitHub Actions scheduling
- **R11. Workflow output** — Vault iteration note + GitHub release artifact + version recommendation
- **R12. GitHub integration** — Read issues/PRs/commits, create releases/tags, auto-create issues
- **R13. Vault integration** — Store iteration history (one note per iteration)
- **R14. Skill/plugin packaging** — Claude skill with `/iterate` command, usable in interactive session

## Scope Boundaries

**In Scope:**
- Version management and release automation (R1–R4)
- Feature proposal generation via AI (R5–R7)
- Progress tracking and release readiness (R8–R9)
- Vault note generation for iteration history
- GitHub API integration (read issues/PRs, create releases/tags, auto-create issues)

**Out of Scope:**
- Automatic code generation for features — developers implement; tool tracks and releases
- Deployment automation — stops at GitHub release; production deployment is separate
- Task breakdown or sprint planning — only tracks milestone-level features
- Multi-repo/monorepo support — single-repo products only
- Custom release workflows — assumes semantic versioning and GitHub releases

## Context & Research

### Relevant Code and Patterns

**Existing Standards:**
- GitHub release flow: `resources/github-發布流程.md` — SemVer conventions, release checklist, CHANGELOG format, commit message standards (must follow)
- Slash command format: `.claude/commands/*.md` (prompt templates executed in Claude session) — reference from `/improve` command in `docs/plans/2026-03-29-001-feat-workflow-self-iteration-plan.md`
- Vault integration: `obsidian-agent patch --heading "Section" --append` for auto-updating iteration notes (session-stop-wrapper pattern)
- CLI architecture: Short-lived process model (each command invocation = new process) — from CSM and `/improve` patterns

**Key Files to Follow:**
- `.claude/commands/improve.md` — Slash command structure and approach pattern
- `resources/github-發布流程.md` — Semantic versioning and changelog conventions
- `docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md` — Vault automation via `obsidian-agent` CLI

### Institutional Learnings

- Stop hooks (session-end) can only run shell commands; Claude reasoning must happen in active session → all analysis in `/iterate` command itself, not in hooks
- Vault integration via `obsidian-agent` is stable and preferred over manual file edits
- Splitting config into layers (Global/Project) requires different rollback strategies: Project = git revert, Global = .bak file
- Version management needs human oversight for dangerous decisions; low-risk suggestions can be fast-applied

### External References

- **GitHub API:** Octokit.js (Node) / PyGithub (Python) — official SDKs with built-in rate limiting and retry
- **Authentication:** Use `GITHUB_TOKEN` in Actions (short-lived, auto-scoped), fine-grained PAT for local tools
- **Version automation:** Release Please (Google-official, monorepo-friendly) or semantic-release (plugin-rich) — both use Conventional Commits
- **Changelog generation:** Conventional Commits + AI polishing is 2026 best practice
- **Rate limiting:** Octokit auto-handles with `throttle` config; implement 3× retry for primary rate limit, 1× for secondary

## Key Technical Decisions

### Decision: Vault as Primary Version Tracker

**Selected:** Vault note as source of truth for current version, last release date, and iteration history

**Rationale:**
- Durable, Git-backed record
- Integrates with existing Obsidian vault for linkable context
- Easier than parsing package.json or git tags for complex state

**Alternative rejected:** Parse version from `package.json` → loses iteration history, less durable in vault context

**Pattern:** Use `type: project` note in `projects/` with frontmatter fields for `version: <semver>`, `last_release: YYYY-MM-DD`, and body sections for iteration log

---

### Decision: Feature Proposals via Claude API (not local heuristics)

**Selected:** `/iterate propose` calls Claude API with context (last release notes, open issues, recent PRs, vault learnings) → returns ranked feature proposals

**Rationale:**
- Developers already track work in GitHub; leverage that data + Claude's reasoning for proposals
- Avoids building custom heuristics for prioritization
- Proposals are personalized to project context (via vault learnings)

**Alternative rejected:** Rule-based heuristics (label counting, issue age) → less intelligent, harder to maintain

**Implementation:** Pass GitHub API data + vault summaries to Claude API, request 3–5 proposals with effort/value estimates

---

### Decision: Auto-Create GitHub Issues for Approved Features

**Selected:** Upon approval, tool automatically creates GitHub issue(s) for each selected feature, assign to next-version milestone

**Rationale:**
- Reduces friction: approve feature → issue exists immediately
- Issue becomes single source of truth for tracking PRs, discussions, completion
- Enables workflow: work on issue → PR closes issue → changelog includes issue #

**Alternative rejected:** Manual issue creation → defeats automation purpose

**Pattern:** Use GitHub API to create issue with title (from proposal), description (problem + requirements), labels, milestone assignment

---

### Decision: Changelog Generation from PRs + Commit Messages

**Selected:** Auto-generate changelog by scanning PRs merged since last release + commit messages (Conventional Commits convention)

**Rationale:**
- Developers already write commit messages and PR titles
- Conventional Commits (feat:, fix:, breaking change:) map directly to changelog categories
- Can be polished by AI before release

**Alternative rejected:** Manual changelog entry → creates duplication with commit history

**Pattern:** Query GitHub API for merged PRs since last tag, extract titles, categorize by type, format as Markdown

---

### Decision: Multi-Step Iteration Flow (Propose → Confirm → Release)

**Selected:** Three separate `/iterate` subcommands:
1. `/iterate propose` — Analyze and propose next features
2. `/iterate confirm` — Review proposals, select features, auto-create issues
3. `/iterate release` — Generate changelog, create GitHub release, update vault

**Rationale:**
- Separates concerns: analysis, approval, execution
- Gives developer time to think between steps
- Allows async workflow: run propose, think overnight, confirm next day

**Alternative rejected:** Single `/iterate` command doing all steps → less flexibility, harder to recover from mistakes

---

### Decision: Version Suggestion (not automatic)

**Selected:** `/iterate release` suggests next version (based on changelog type: major/minor/patch) but developer confirms

**Rationale:**
- Semantic versioning has business semantics humans must decide (is this breaking? is this worth a major?)
- AI can suggest, human must approve

**Pattern:** Generate changelog, analyze commit messages, suggest version bump, prompt developer for confirmation

---

### Decision: Vault-Based Iteration History (not database)

**Selected:** One vault note per iteration (date-stamped: `2026-03-30-v1.2.3-iteration.md`) recording: proposals, selections, release metadata

**Rationale:**
- Integrates with existing vault for browsing and linking
- Git-backed, searchable
- No external service required

**Pattern:** Use `type: project` + `subtype: iteration-log` (new subtype), frontmatter records version/date/proposals/release-url

---

## High-Level Technical Design

```
User triggers `/iterate propose`
  ↓
Vault: Read current version + last release date from project note
  ↓
GitHub API:
  - Fetch open issues (filter: feature requests)
  - Fetch closed PRs since last release tag
  - Fetch vault learnings (via search)
  ↓
Claude API: Analyze context → generate 3-5 feature proposals (title, problem, effort, value, rationale)
  ↓
Output: Render proposals to user with effort/value matrix and rationale
════════════════════════════════════════════════════════════════

User triggers `/iterate confirm`
  ↓
Display proposals from previous run
  ↓
User: Select which features to build, reorder by priority
  ↓
GitHub API: For each selected feature:
  - Create new GitHub issue (title, description, labels)
  - Assign to next-version milestone
  ↓
Vault: Create iteration note (record: date, proposals, selections)
  ↓
Output: Confirm issues created, show iteration history note link
════════════════════════════════════════════════════════════════

User triggers `/iterate release` (after features are complete)
  ↓
GitHub API: Fetch merged PRs since last release tag
  ↓
Changelog Generator:
  - Parse commit messages (Conventional Commits format)
  - Categorize: Added/Changed/Fixed/Removed/Breaking Changes
  - Generate Markdown changelog
  ↓
Version Suggester: Analyze changelog → suggest MAJOR/MINOR/PATCH bump
  ↓
User: Confirm version number
  ↓
GitHub API:
  - Create git tag with version
  - Create GitHub release (with auto-generated changelog as body)
  - Link to milestone
  ↓
Vault:
  - Update project note: current version, last release date
  - Append release to iteration history note
  ↓
Output: GitHub release URL, updated vault note link
```

---

## Implementation Units

- [ ] **Unit 1: Vault Iteration System Initialization**

**Goal:** Set up vault project note structure to track version and iteration history

**Requirements:** R1, R13

**Dependencies:** None

**Files:**
- Create: `templates/iteration-log.md` — Template for iteration notes
- Create: `projects/<product-name>/product-version.md` — Project-level version tracker (if not exists)
- Modify: `CONVENTIONS.md` — Document new `iteration-log` subtype for `project` notes

**Approach:**
- Define iteration note frontmatter: `type: project`, `subtype: iteration-log`, `date: YYYY-MM-DD`, `version: X.Y.Z`, `proposals: <count>`, `selected: <count>`, fields for tracking proposals and release metadata
- Create project version note template with sections: Current Version, Last Release Date, Iteration History Links, Next Planned
- Use `obsidian-agent` CLI to create and update notes (pattern: `obsidian-agent patch` for appends)
- Integration: `/iterate` commands read/update this note using `obsidian-agent` CLI, not manual file edits

**Patterns to follow:**
- Frontmatter structure from `CONVENTIONS.md` (use `type: project`, not new type)
- `obsidian-agent patch --heading "Iteration History" --append "..."` pattern from session-stop-wrapper
- `obsidian-agent note` command for creating new iteration notes

**Test scenarios:**
- Happy path: Create project version note, frontmatter is valid YAML, fields parse correctly
- Happy path: Append iteration entry to history section, note remains valid Markdown, linked correctly
- Edge case: Project version note doesn't exist yet → `/iterate propose` can create it with defaults (version = 0.1.0)
- Edge case: Vault not initialized → `/iterate` detects and prompts user to initialize

**Verification:**
- Project version note exists with correct frontmatter
- `obsidian-agent` CLI can read and append to iteration notes without errors
- Iteration notes render correctly in Obsidian with all backlinks intact

---

- [ ] **Unit 2: GitHub API Integration Layer**

**Goal:** Stable wrapper around GitHub API for reading issues/PRs, creating releases, managing tags

**Requirements:** R3, R12

**Dependencies:** None (standalone module)

**Files:**
- Create: `.claude/lib/github-api.js` (or `.py` if Python) — GitHub API wrapper module
- Create: `.claude/lib/github-api.test.js` — Test suite
- Modify: `.claude/config.json` (or similar) — Store GitHub token env var reference

**Approach:**
- Wrap Octokit.js (Node) or PyGithub (Python) with higher-level functions:
  - `getLastRelease(owner, repo)` → returns tag, date, release notes
  - `getClosedPRsSince(owner, repo, sinceDate)` → returns list of merged PRs with titles, authors
  - `getOpenIssuesByLabel(owner, repo, label)` → returns feature request issues
  - `createRelease(owner, repo, tagName, changelog, versionName)` → creates release and tag
  - `createIssue(owner, repo, title, body, labels, milestone)` → creates issue
  - `getReleaseReadiness(owner, repo, milestone)` → checks if PRs in milestone are merged and checks pass

- Handle authentication: read `GITHUB_TOKEN` env var (provided by GitHub Actions or user)
- Include rate limiting and retry logic (auto-handled by Octokit, but document assumptions)
- Error handling: Catch API errors, retry on rate limit (use Octokit's built-in throttle), surface meaningful errors to user

**Patterns to follow:**
- Octokit.js rate-limit retry pattern (3× for primary, 1× for secondary)
- GitHub API v2026-03-10 or later (ensure modern endpoint behavior)
- Similar wrapper pattern as existing integrations in the project

**Test scenarios:**
- Happy path: `getLastRelease()` returns correct tag name, date, and release body
- Happy path: `getClosedPRsSince()` filters by date correctly, returns merged PRs with titles
- Happy path: `createRelease()` creates GitHub release with tag, callable content in release body
- Error path: Missing `GITHUB_TOKEN` → surface clear error message
- Error path: Rate limited (GitHub returns 429) → auto-retry after `Retry-After` seconds
- Edge case: No previous release (first release) → `getLastRelease()` returns null, code handles gracefully
- Edge case: Private repo with limited PAT scopes → GitHub API returns 403, error message indicates scope issue
- Integration: `createIssue()` creates issue that links to milestone, appears in GitHub web UI

**Verification:**
- All functions callable from `/iterate` command
- API errors caught and logged with context
- Rate limiting does not block normal operation
- GitHub release created by unit contains correct tag, title, body (changelog)

---

- [ ] **Unit 3: AI Feature Proposal Engine**

**Goal:** Analyze last release and open issues; generate ranked feature proposals via Claude API

**Requirements:** R5, R6

**Dependencies:** Unit 2 (GitHub API), vault access

**Files:**
- Create: `.claude/lib/proposal-engine.js` (or `.py`) — Proposal generation logic
- Create: `.claude/lib/proposal-engine.test.js` — Test suite

**Approach:**
- Function: `generateProposals(githubContext, vaultContext)` → returns list of proposal objects
  - Input: Last release notes, open issues (titles + labels), closed PRs since last release, vault learnings (search results from vault notes)
  - Process: Build context prompt, call Claude API (gpt-4-turbo or latest), parse response into structured proposals
  - Output: Array of proposals, each with: title, problem statement, estimated effort (S/M/L), estimated value (L/M/H), prioritization rank, rationale

- Proposal generation prompt template (in `.claude/commands/iterate.md` or separate file):
  - Last release: what shipped, what was fixed, what changed
  - Open issues: new feature requests, improvements
  - Recent completed work: what devs accomplished
  - Vault learnings: any project-specific context (research, architectural decisions)
  - Instruction: "Propose 3-5 features for next version ranked by value/effort ratio"

- Parsing: Claude returns structured text (numbered list + estimation + rationale), parse into JSON

**Patterns to follow:**
- Claude API integration pattern from existing Claude Code tools
- Structured prompting (define output format clearly)
- Vault search integration (use `obsidian-agent search` to gather context)

**Test scenarios:**
- Happy path: Given last release, open issues, and vault context → generate 5 proposals with effort/value estimates
- Happy path: Proposals are ranked by priority (value/effort ratio or explicitly stated ranking)
- Happy path: Proposals include problem statement and rationale
- Edge case: No open issues → proposals are based on vault learnings + team patterns
- Edge case: First release (no last release to compare) → proposals based on vault project goals
- Edge case: Claude API rate limited → graceful degradation, fewer proposals, or queued retry
- Integration: Proposals can be presented to user in `/iterate propose` command

**Verification:**
- Proposal output is well-structured (can be parsed and rendered)
- Effort estimates are realistic (S ≈ <1 day, M ≈ 1-3 days, L ≈ 1+ week)
- Value estimates are explained (links to issues, vault context)
- Proposals are actionable (developer can immediately create issue from proposal)

---

- [ ] **Unit 4: Changelog Generation**

**Goal:** Auto-generate human-readable changelog from merged PRs and commit messages

**Requirements:** R2, R3

**Dependencies:** Unit 2 (GitHub API)

**Files:**
- Create: `.claude/lib/changelog-generator.js` (or `.py`) — Changelog generation
- Create: `.claude/lib/changelog-generator.test.js` — Test suite

**Approach:**
- Function: `generateChangelog(owner, repo, sinceTag, untilTag)` → returns Markdown changelog

- Process:
  1. Fetch merged PRs between two tags (API: `GET /repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc`)
  2. For each PR, extract: title, labels, PR number, author
  3. Categorize by Conventional Commits type (from PR title or commit messages):
     - **Breaking Changes**: Lines starting with `BREAKING CHANGE:` or commits with `!:` notation
     - **Features**: `feat:` commits / `type: feature` label
     - **Fixes**: `fix:` commits / `type: bug` label
     - **Improvements**: `refactor:`, `perf:`, `docs:` (optional, can merge into Features or skip)
  4. Generate Markdown sections with categorized entries:
     ```markdown
     ## v1.2.0 (YYYY-MM-DD)

     ### Breaking Changes
     - Issue with X (#123)

     ### Features
     - New feature Y (#124)

     ### Bug Fixes
     - Fixed Z (#125)
     ```
  5. Allow AI polish: pass generated changelog to Claude for readability improvement (optional, can skip for MVP)

- Error handling: If commit message format is inconsistent, use PR title as fallback; categorize as "Other" if unclear

**Patterns to follow:**
- GitHub release flow conventions from `resources/github-發布流程.md` (category order, format)
- Conventional Commits spec (https://www.conventionalcommits.org/)

**Test scenarios:**
- Happy path: Fetch 10 PRs since last tag, group by category (feature/fix), generate markdown changelog
- Happy path: Changelog includes PR numbers (e.g., `#123`) which become GitHub links
- Happy path: Breaking changes appear prominently at top
- Edge case: PR title is inconsistent format → fall back to first commit message in PR
- Edge case: No PRs since last release → changelog says "No changes" or "Patch release"
- Edge case: Many PRs (100+) → paginate or summarize (show top 20, note "and X more")
- Integration: Generated changelog can be used as GitHub release body

**Verification:**
- Changelog is valid Markdown (renders without errors)
- Categories are present and correctly grouped
- PR links are correct (reference valid issue numbers)
- Breaking changes are flagged clearly

---

- [ ] **Unit 5: Version Suggestion Engine**

**Goal:** Suggest next semantic version based on changelog content

**Requirements:** R2, R10

**Dependencies:** Unit 4 (Changelog)

**Files:**
- Create: `.claude/lib/version-suggester.js` (or `.py`) — Version suggestion logic
- Create: `.claude/lib/version-suggester.test.js` — Test suite

**Approach:**
- Function: `suggestVersion(currentVersion, changelog)` → returns suggested version string

- Logic:
  1. Parse current version (SemVer: X.Y.Z)
  2. Analyze changelog categories:
     - Breaking changes present? → increment MAJOR
     - Features present? → increment MINOR (if MAJOR not incremented)
     - Only fixes? → increment PATCH (if MAJOR/MINOR not incremented)
     - No changes? → keep version or increment PATCH
  3. Return suggested version (e.g., "1.3.0") and reasoning (e.g., "Minor bump: 3 features, no breaking changes")

- Handle edge cases:
  - `0.x.y` versions (early development): breaking changes still increment minor, fixes increment patch
  - Pre-release versions (e.g., `1.0.0-alpha`): document handling (usually increment to stable or next pre-release)

**Patterns to follow:**
- Semantic Versioning spec (https://semver.org/)
- Conventional Commits mapping to SemVer (feat → MINOR, fix → PATCH, breaking → MAJOR)

**Test scenarios:**
- Happy path: Current 1.0.0 + 3 features + 2 fixes → suggest 1.1.0
- Happy path: Current 1.0.0 + breaking changes → suggest 2.0.0
- Happy path: Current 1.0.0 + 1 fix → suggest 1.0.1
- Edge case: Current 0.5.0 (pre-release) + features → suggest 0.6.0
- Edge case: No changes in changelog → suggest patch bump or keep same version
- Verification: Suggested version is always greater than current version

---

- [ ] **Unit 6: `/iterate` Slash Command**

**Goal:** Implement the user-facing command with subcommands: propose, confirm, release

**Requirements:** R10, R11, R13, R14

**Dependencies:** Units 1–5 (all supporting modules)

**Files:**
- Create: `.claude/commands/iterate.md` — Main slash command definition
- Modify: `.claude/CLAUDE.md` — Register `/iterate` in Slash Commands table

**Approach:**
- Slash command format (follow `.claude/commands/improve.md` pattern):
  - Description
  - Three subcommands: `propose`, `confirm`, `release`
  - Environment setup (validate `GITHUB_TOKEN`, vault path)
  - Execution logic using supporting modules

- **`/iterate propose`** subcommand:
  - Read vault: current version, last release date from project note
  - Call GitHub API: get last release, open issues, closed PRs since release
  - Call proposal engine: generate 3–5 proposals
  - Call AI: optionally rank proposals
  - Output: Render proposals to user in table/list format (title, problem, effort, value, rank)
  - Vault: Create iteration note recording proposals

- **`/iterate confirm`** subcommand:
  - Load previous proposals from iteration note
  - Prompt user to select features (checkboxes or numbered selection)
  - Call GitHub API: create issues for each selected feature
  - Assign issues to next-version milestone
  - Output: Confirm issues created, show GitHub links
  - Vault: Update iteration note with selections

- **`/iterate release`** subcommand:
  - Validate: all selected features are complete (milestone PRs merged)
  - Call changelog generator: create changelog from PRs since last release
  - Call version suggester: suggest next version
  - Prompt user: confirm version number
  - Call GitHub API: create release with tag and changelog
  - Vault: update project version note, append to iteration history
  - Output: GitHub release URL, vault iteration note link

- Error handling:
  - Missing `GITHUB_TOKEN` → clear error, link to setup docs
  - Not a git repo → detect and surface error
  - Vault not initialized → offer to initialize
  - No approved features yet → suggest running `/iterate confirm` first

**Patterns to follow:**
- Slash command structure from `.claude/commands/improve.md`
- On-demand execution in active Claude session (do NOT use stop hooks)
- Use `obsidian-agent` CLI for vault operations
- Reference module imports (`require('./lib/github-api.js')` or similar)

**Test scenarios:**
- Happy path: `/iterate propose` → presents 3–5 proposals with effort/value estimates
- Happy path: User selects 2 features → `/iterate confirm` → creates 2 GitHub issues in next-version milestone
- Happy path: Features are merged → `/iterate release` → suggests version 1.1.0 → user confirms → GitHub release created, vault updated
- Edge case: `/iterate release` when not all features are done → alert user, show which PRs are still open
- Edge case: GitHub rate limit hit → retry automatically, inform user if still blocked
- Integration: Full workflow from propose to release works end-to-end

**Verification:**
- `/iterate propose` returns structured proposals (parseable as table)
- `/iterate confirm` creates actual GitHub issues (checkable in web UI)
- `/iterate release` creates actual GitHub release (visible on GitHub)
- Vault notes are created and linked correctly

---

- [ ] **Unit 7: Integration Testing and Validation**

**Goal:** End-to-end testing of full iteration workflow; validate all pieces work together

**Requirements:** All (R1–R14)

**Dependencies:** Units 1–6

**Files:**
- Create: `test/e2e-iteration-workflow.test.js` — End-to-end test
- Create: `test/fixtures/sample-github-context.json` — Mock GitHub API responses
- Create: `test/fixtures/sample-vault.md` — Sample vault project note

**Approach:**
- Mock GitHub API responses (use recorded responses or fixtures)
- Test full workflow:
  1. Initialize vault project note (version 1.0.0)
  2. Run `/iterate propose` with mock issues/PRs → check proposals are generated
  3. Run `/iterate confirm` selecting features → check issues are created
  4. Simulate merged PRs (mock GitHub API responses)
  5. Run `/iterate release` → check version suggested, release created, vault updated

- Validation:
  - Vault note structure is correct after each step
  - GitHub API calls are well-formed
  - Changelog is valid Markdown
  - Version increments are correct
  - All error paths are handled gracefully

**Test scenarios:**
- Happy path: Full iteration cycle (propose → confirm → release)
- Integration: Vault and GitHub APIs work together
- Edge case: Release with no new features (patch bump)
- Edge case: Release with breaking changes (major bump)
- Error recovery: User cancels partway through, can restart
- Cross-system consistency: GitHub issues and vault notes agree on feature list

**Verification:**
- Workflow completes without errors
- All artifacts created (GitHub release, vault notes)
- Data consistency across GitHub and vault
- Rollback (if implemented) works cleanly

---

## System-Wide Impact

- **Interaction graph:** Developer triggers `/iterate propose` → Claude analyzes GitHub + vault → proposals shown → `/iterate confirm` auto-creates issues → PRs flow into milestone → `/iterate release` creates GitHub release + updates vault
- **Error propagation:** API errors (GitHub rate limit, missing token) caught in command execution, clear messages to user. Vault errors escalate as unsaved state warning.
- **State lifecycle risks:** Partial iteration (propose but no confirm, or confirm but no release) leaves vault note in incomplete state; user should be able to resume. Implement idempotency: re-running `/iterate confirm` should not duplicate issues.
- **API surface parity:** `/iterate propose`, `/iterate confirm`, `/iterate release` are all available in Claude Code interactive session
- **Integration coverage:** End-to-end test validates full propose→confirm→release workflow
- **Unchanged invariants:** GitHub release creation process unchanged (still creates tag + release); vault project notes remain queryable via `obsidian-agent`; Conventional Commits usage unchanged; no impact on existing slash commands

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| GitHub API rate limiting blocks workflow | Octokit built-in retry + exponential backoff; document rate limits in help text |
| User forgets to approve proposals, features accumulate | Iteration note tracks all proposals; `/iterate status` shows pending items (future enhancement) |
| Vault not initialized → command fails | Detect missing project note, offer to initialize with defaults |
| Version conflicts (user edits version manually vs. tool) | Version source of truth: git tag (GitHub) or package.json, vault is secondary; document this clearly |
| Breaking changes missed in changelog | Validate commit message format (Conventional Commits); require `BREAKING CHANGE:` or `!:` notation; remind user during release review |
| GitHub token exposed in logs | Use masked environment variable; never log full token; document security best practices |

## Open Questions

### Resolved During Planning

- **Triggering mechanism:** On-demand `/iterate` command (active session) — chosen to align with existing slash command pattern and ensure Claude is available for reasoning
- **Version storage:** Vault project note + git tag (package.json, Git tag) — vault for iteration history, git for source-of-truth version
- **GitHub authentication:** `GITHUB_TOKEN` env var (set by GitHub Actions or user for local) — follows standard GitHub CLI pattern
- **Changelog format:** GitHub release body (Markdown) — no separate CHANGELOG.md to maintain

### Deferred to Implementation

- **Multi-language support:** Initial release English-only; i18n deferred
- **Custom changelog templates:** MVP uses fixed categories (Features/Fixes/Breaking); customizable templates deferred
- **Scheduled releases:** MVP is on-demand only; GitHub Actions integration deferred

## Dependencies / Assumptions

- Project uses GitHub for issues and releases (not GitLab, Gitea, etc.)
- Vault is initialized and Git-backed (can commit iteration notes)
- Developer has `GITHUB_TOKEN` available (from Actions or personal)
- Project follows Conventional Commits for commit messages (required for accurate categorization)
- Project uses semantic versioning (MAJOR.MINOR.PATCH format)

## Sources & References

- **Origin document:** docs/brainstorms/2026-03-30-product-iteration-automation-requirements.md
- **GitHub release standards:** resources/github-發布流程.md
- **Vault integration pattern:** docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md
- **Slash command pattern:** docs/plans/2026-03-29-001-feat-workflow-self-iteration-plan.md (reference `/improve` implementation)
- **GitHub API docs:** https://docs.github.com/en/rest
- **Octokit.js:** https://github.com/octokit/octokit.js
- **Conventional Commits:** https://www.conventionalcommits.org/
- **Semantic Versioning:** https://semver.org/
