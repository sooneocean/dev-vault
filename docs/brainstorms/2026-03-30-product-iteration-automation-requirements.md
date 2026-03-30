---
title: "Product Iteration Automation Workflow"
date: 2026-03-30
topic: product-iteration-automation
---

# Product Iteration Automation Workflow

## Problem Frame

Individual developers manage product versioning manually: writing changelog entries, creating GitHub releases, tagging versions, brainstorming next-version features, and maintaining release notes. This is repetitive, error-prone, and breaks development flow. There's no systematic way to:
- Track version milestones and feature completion
- Propose next-version features based on current state (issues, PRs, user feedback)
- Automate release creation and changelog generation
- Loop seamlessly from planning → development → release → next planning

**Target user:** Solo developer or small team shipping products via GitHub.

## Requirements

### Version & Release Management

- **R1. Version state tracking** — Tool maintains current version, last release date, and list of features completed since last release
- **R2. Automatic changelog generation** — Based on completed PRs/features, generate human-readable changelog entries (organized by category: features, fixes, breaking changes, etc.)
- **R3. GitHub release automation** — Create GitHub release with auto-generated changelog, semantic version tag, and release notes
- **R4. Rollback support** — Ability to undo a release (delete tag/release on GitHub, revert version state in tool)

### Feature Planning & Proposal

- **R5. AI-powered feature proposal** — Tool analyzes:
  - Last released version (features, fixes, breaking changes)
  - Open GitHub issues (feature requests, bugs, improvements)
  - Closed PRs since last release (what was done)
  - Vault learnings/research notes (any domain-specific learnings)

  Then generates 3–5 feature proposals for the next version, ranked by value/effort estimate

- **R6. Feature proposal presentation** — Proposals include:
  - Title and 1-line description
  - Problem this solves
  - Estimated effort (small/medium/large)
  - Estimated user value (low/medium/high)
  - Why it's prioritized relative to others

- **R7. Manual feature confirmation** — Developer approves/rejects/ranks proposed features, creates GitHub milestones and issues for selected features

### Development & Progress Tracking

- **R8. Feature progress tracking** — Tool tracks:
  - Features in progress (which GitHub milestone + PR count)
  - Completed features (linked PR/commits since last release)
  - Remaining work (open issues in milestone)

- **R9. Release readiness check** — Tool indicates:
  - Is the current feature set ready to release? (All planned features completed + tests passing)
  - What's blocking release? (Open PRs, failed checks, incomplete features)

### Workflow Automation

- **R10. Scheduled iteration loop** — Tool supports periodic workflow triggering:
  - Manual trigger (`/iterate` command)
  - Optional scheduled trigger (e.g., weekly, on-demand)
  - Generates workflow summary at each phase (proposal → confirmation → release)

- **R11. Workflow output** — Each iteration produces:
  - Vault note documenting: what was proposed, what was selected, what was shipped
  - GitHub release artifact
  - Next recommended version number

### Integration Points

- **R12. GitHub integration** — Tool reads/writes:
  - Issues and PRs (filter by milestone, label, state)
  - Release and tag API
  - Commit history (to populate changelog)

- **R13. Vault integration** — Tool stores:
  - Iteration history (one note per iteration: proposal set, selections, release metadata)
  - Feature planning context (links to related vault notes, research)

- **R14. Skill/Plugin packaging** — Tool packaged as:
  - Claude skill (`/iterate` command in Claude Code)
  - Usable in interactive session (propose features, confirm, release)
  - Optional GitHub Actions trigger for scheduled runs

## Success Criteria

- Individual developer can complete a full iteration cycle (propose → select → release) in <30 min, with most automation handled by the tool
- Generated changelogs are human-readable and need minimal editing
- Feature proposals are relevant and ranked sensibly
- Release artifacts (GitHub release, tag, vault notes) are complete and correct
- Tool gracefully handles edge cases (first release, no issues, no changes since last release, etc.)

## Scope Boundaries

### In Scope
- Version management and release automation (R1–R4)
- Feature proposal generation (R5–R7)
- Progress tracking and release readiness check (R8–R9)
- Vault note generation for iteration history
- GitHub API integration (read issues/PRs, create releases/tags)

### Deliberately Out of Scope
- **Automatic code generation for features** — Developers implement features; tool just tracks and releases
- **Deployment automation** — Tool stops at GitHub release; deploying to production is out of scope
- **Detailed project management** — Doesn't manage task breakdown, sprint planning, or resource allocation
- **Multi-project support** — Designed for single product per tool instance (can be extended later)
- **Custom release workflows** — Assumes standard semantic versioning and GitHub-based releases
- **Multi-repo monorepos** — Focuses on single-repo products

## Key Decisions

### Decision: Feature Proposal via AI Analysis vs. Manual Entry
**Selected:** AI analysis of issues/PRs + manual confirmation
- **Why:** Developers already track work in GitHub; AI proposal saves brainstorming time without requiring structured input
- **Alternative:** Manual feature entry → more control, higher friction, less automation value

### Decision: When to Propose Features
**Selected:** At release time (after shipping current version)
- **Why:** Clean boundary; proposals are for *next* version, not speculative
- **Alternative:** Continuous brainstorming → more context, but harder to scope per-version release

### Decision: Vault Note Format for Iteration History
**Selected:** One structured note per iteration (proposal → selection → release)
- **Why:** Durable record, linkable from projects/areas, searchable history
- **Alternative:** GitHub releases only → simpler, less vault integration

### Decision: Semantic Versioning Strategy
**Selected:** Tool suggests next version number based on change type (MAJOR/MINOR/PATCH); developer confirms
- **Why:** Follows conventions; tool avoids guessing semver semantics
- **Alternative:** Full auto-increment → less control, risk of wrong version bump

## Dependencies & Assumptions

- Project uses semantic versioning (e.g., 1.2.3)
- Features/fixes tracked as GitHub issues or PRs
- Developer has GitHub API token with repo read/write access
- Vault exists and is initialized (for iteration history notes)
- Current version is tracked somewhere (e.g., `package.json`, Git tag, vault project note)

## Outstanding Questions

### Resolved During Brainstorm

- **Version storage:** Dedicated vault (obsidian-agent CLI) as version tracker
  - Vault note tracks: current version, last release date, milestones, feature status
  - Why: Durable record integrated with other project notes, searchable, Git-backed

- **Changelog format:** GitHub release description (auto-generated from PR/commit metadata)
  - Why: Cleaner workflow (no separate CHANGELOG.md to maintain), integrated with release artifacts

- **Auto-create GitHub issues:** Yes
  - Why: Developer confirms features → tool auto-creates issues in selected milestone
  - Reduces friction and ensures tracked work matches approved features

### Deferred to Planning
- **How to handle breaking changes in changelog generation?** (Separate section? Highlight? Special badge?) — needs more context during implementation
- **Multi-language support for proposals?** (Just English for MVP?) — can be addressed after initial release
- **Offline mode?** (Tool works without GitHub connectivity?) — evaluate during scoping

## Next Steps

→ **User decision:** Answer the three "Resolve Before Planning" questions above, then proceed to `/ce:plan` for detailed implementation planning.

Alternatively, if you want to iterate on the feature set further:

→ **Continue brainstorm** to refine scope, explore alternatives, or dig into edge cases before planning.
