---
title: "feat: SEO Orchestrator Skill — Phase 1 MVP"
type: feat
status: active
date: 2026-04-12
origin: docs/brainstorms/2026-04-12-seo-orchestrator-skill-requirements.md
---

# feat: SEO Orchestrator Skill — Phase 1 MVP

## Overview

Unify 4 existing WordPress SEO optimization scripts into a single conversational `/seo` skill for Claude Code. Replace the current CLI wrapper (`site-optimizer.js`) and eliminate "coming soon" stubs for meta-tags and schema-markup. Add shared utilities, backup/rollback for all modules, and deprecate ~51 superseded scripts.

## Problem Frame

The current SEO tooling is fragmented: 56 scripts in `scripts/` with no unified entry point, inconsistent auth/retry patterns, and 2 of 4 optimization types throwing "coming soon" errors despite the logic existing in separate phase4 scripts. Users must know which script to run, with what flags, in what order. (see origin: `docs/brainstorms/2026-04-12-seo-orchestrator-skill-requirements.md`)

## Requirements Trace

- R1. Single `/seo` entry point accepting natural language
- R2. Conversational mode: analyze → suggest → confirm before batch writes
- R5. Image ALT module (extract from `image-alt-text-optimizer.js`)
- R6. Meta Tags module (extract from `phase4-complete-seo-batch-generator.js` + `phase4-apply-seo-to-wordpress.js`)
- R7. Schema Markup module (extract from same phase4 scripts)
- R8. Internal Links module (extract from `internal-linker-v2.js`)
- R13. Shared utilities (API fetch, backup, reporting) — not a unified interface
- R14. Every module independently rollbackable with pre-execution backup
- R15. No hard dependencies between modules
- R19. Structured summary report after execution
- R21. Script deprecation plan

## Scope Boundaries

- Phase 1 only — no health score (R3), priority matrix (R4), or new modules (R9-R12)
- No wpcom-mcp for writes — direct REST API only (per-write confirmation conflict)
- WordPress.com only (yololab.net primarily)
- No persistent history or NL querying (Phase 2)
- No automated scheduling

## Context & Research

### Relevant Code and Patterns

| File | Lines | Role | Key Patterns |
|------|-------|------|-------------|
| `scripts/image-alt-text-optimizer.js` | 1,258 | Image ALT optimization | Auth discovery (4 sources), retry with backoff, file locking, backup/rollback, resume, post-verification |
| `scripts/internal-linker-v2.js` | 519 | Internal link injection | Rate limiting, state management, NO rollback |
| `scripts/phase4-complete-seo-batch-generator.js` | ~400 | Meta/schema/OG generation | Claude API text generation, batch processing, JSON output |
| `scripts/phase4-apply-seo-to-wordpress.js` | 270 | Meta/schema application | Yoast SEO field writes (`_yoast_wpseo_*`), WP.com v1.1 API |
| `scripts/site-optimizer.js` | 280 | Current CLI router | Arg parsing, `execSync` dispatch, config loading |
| `.claude/lib/site-optimizer-command.js` | 78 | Current skill command | `spawn` wrapper, predefined shortcuts |
| `.claude/skills/site-optimizer-config.json` | 83 | Site config | Multi-site support, optimization type registry |

### Institutional Learnings

- **Rate limits proven:** `batch:5, delay:2000ms, retries:3, backoff:3000ms` achieved 100% success across 2,728 articles (from `image-alt-text-optimizer.js`)
- **API version mixing required:** v1.1 for media `alt` field; wp/v2 with `context=edit` for raw Gutenberg content. Never write rendered HTML back — destroys block structure
- **Wrapper over rewrite validated:** `session-stop-wrapper` solution confirms thin wrappers are lower risk than core rewrites (from `docs/solutions/`)
- **Backup must persist per-batch, not per-run:** If batch fails mid-execution, only per-batch backup allows partial rollback

### Auth Patterns (3 implementations, need unification)

| Script | Env Vars | Methods | API Base |
|--------|----------|---------|----------|
| image-alt | `WP_APP_USER`/`WP_APP_PASS`, `WP_BEARER_TOKEN`/`WPCOM_TOKEN`, `.mcp.json` | Basic + Bearer | Dynamic (direct wp-json or WP.com proxy) |
| internal-linker | `WP_APP_USER`/`WP_APP_PASS`, `WP_BEARER_TOKEN`, `.mcp.json` | Basic + Bearer | WP.com proxy only |
| phase4-apply | `WPCOM_TOKEN` only | Bearer only | WP.com v1.1 |

## Key Technical Decisions

- **REST API for all writes, not wpcom-mcp:** wpcom-mcp requires per-write user confirmation, making batch operations (2,728 articles) impractical. MCP can be used for discovery (listing sites, checking capabilities) but all read/write operations go through direct REST API. (see origin: Key Decisions — API channel strategy)
- **Shared utilities, not unified interface:** Each module keeps its natural workflow (image-alt has 6 phases, internal-linker has 4, phase4 has generate+apply). Shared utilities handle cross-cutting concerns: auth, fetch+retry, backup, state, locking. (see origin: Key Decisions — shared utilities)
- **Wrap, don't rewrite:** Export async functions from existing scripts. The 1,258-line image-alt optimizer is production-proven — refactoring it to fit a 5-step interface risks regressions with no benefit. (see origin: Key Decisions — extract existing logic)
- **Skill prompt template, not executable script:** The `/seo` skill is a Claude Code skill prompt (markdown in `.claude/skills/`) that guides Claude through conversational SEO optimization. Claude calls module scripts as tools, not as subprocesses.
- **Cached quick audit:** Full-site scan of 2,728 articles across 4 modules would take 30+ minutes. Use cached scan results (<7 days old) when available; otherwise sample 100 articles and extrapolate.
- **Global lock:** Single `seo-orchestrator.lock` file with 8-hour TTL, replacing per-module lock files. Prevents concurrent SEO writes from multiple sessions.

## Open Questions

### Resolved During Planning

- **Yoast SEO field support:** `phase4-apply-seo-to-wordpress.js` already successfully writes `_yoast_wpseo_title`, `_yoast_wpseo_metadesc`, and `_yoast_wpseo_schema` to yololab.net. This confirms the WordPress.com plan supports Yoast fields. Unit 3 includes a verification step before first batch write.
- **Internal links rollback:** Will save full `post.content` to backup JSON before injection. Large (~50-100MB for 2,728 articles) but necessary for rollback safety.
- **Session persistence:** `seo-orchestrator-state.json` stores active module, batch progress, and user intent. The skill checks this file on `/seo` entry and offers resume.
- **Auth standardization:** Unify on `WPCOM_TOKEN` as the canonical env var. The shared auth module accepts `WPCOM_TOKEN`, `WP_BEARER_TOKEN`, `WP_APP_USER`+`WP_APP_PASS`, and `.mcp.json` fallback (in that order).
- **Quick audit scope:** Sample 100 articles when no cache exists. Cache results to `seo-optimization-output/audit-cache.json` with timestamp.

### Deferred to Implementation

- **Exact function signatures** for module wrapper exports — depends on seeing how cleanly globals can be replaced with parameters
- **Optimal sample size for quick audit** — 100 is a starting point; may adjust based on variance in real data
- **Rate limit budget sharing** — current plan uses per-module limits; may need a shared rate limiter if 429s are site-wide

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
/seo skill prompt (Claude Code skill)
  │
  ├─ Quick Audit (sample or cached)
  │   ├─ image-alt: check N articles for missing/weak ALT
  │   ├─ meta-tags: check N articles for missing meta title/desc
  │   ├─ schema: check N articles for missing JSON-LD
  │   └─ internal-links: check N articles for missing 延伸閱讀
  │
  ├─ User Confirmation (count, time, cost, 3 samples)
  │
  ├─ Execute Module (one at a time)
  │   ├─ shared-utils: auth, fetch+retry, backup, lock, state
  │   ├─ module script: image-alt | meta-tags | schema | links
  │   └─ report: structured summary per module
  │
  └─ Orchestrator State
      └─ seo-orchestrator-state.json (cross-session resume)
```

```
scripts/
├─ lib/
│   └─ seo-shared.js          ← NEW: shared utilities
├─ modules/
│   ├─ image-alt.js            ← NEW: thin wrapper
│   ├─ meta-tags.js            ← NEW: thin wrapper
│   ├─ schema-markup.js        ← NEW: thin wrapper
│   └─ internal-links.js       ← NEW: thin wrapper
├─ image-alt-text-optimizer.js ← KEEP: core logic (imported by wrapper)
├─ internal-linker-v2.js       ← KEEP: core logic (imported by wrapper)
├─ phase4-complete-seo-batch-generator.js  ← KEEP: generation logic
├─ phase4-apply-seo-to-wordpress.js        ← KEEP: application logic
├─ site-optimizer.js           ← DEPRECATE after skill is functional
└─ _deprecated/                ← 51 superseded scripts moved here
```

## Implementation Units

- [ ] **Unit 1: Shared Utilities Module**

**Goal:** Extract cross-cutting utilities from `image-alt-text-optimizer.js` into a shared module that all 4 module wrappers import.

**Requirements:** R13 (shared utilities)

**Dependencies:** None — this is the foundation

**Files:**
- Create: `scripts/lib/seo-shared.js`
- Test: `test/seo-shared.test.js`

**Approach:**
- Extract from `image-alt-text-optimizer.js`: auth discovery (lines 90-130), `apiGet`/`apiPost` with retry+backoff (lines 135-200), `sleep`, `log`, `ensureDir`, `saveJSON`/`loadJSON`, `acquireLock`/`releaseLock`
- Auth priority: `WPCOM_TOKEN` → `WP_BEARER_TOKEN` → `WP_APP_USER`+`WP_APP_PASS` → `.mcp.json` extraction
- `apiGet(base, endpoint, headers)` / `apiPost(base, endpoint, body, headers)` — configurable base URL for v1.1 vs wp/v2
- Rate limit config as parameter: `{ batchSize, delayMs, retries, backoffMs }`
- Backup helper: `createBackup(filepath, entries)`, `loadBackup(filepath)`, `appendBackup(filepath, entry)`
- State helper: `loadState(filepath)`, `saveState(filepath, state)` with processed/failed/skipped arrays
- Global lock: `acquireGlobalLock(lockPath, ttlMs)`, `releaseGlobalLock(lockPath)`
- Auth health check: `verifyAuth(config) → { ok, method, apiBase, error }`
- All functions accept config parameter — no global state, no hardcoded site IDs

**Patterns to follow:**
- Auth discovery logic from `image-alt-text-optimizer.js` lines 90-130
- Retry pattern from `image-alt-text-optimizer.js` `apiGet`/`apiPost`
- Lock pattern from `image-alt-text-optimizer.js` `acquireLock`/`releaseLock`

**Test scenarios:**
- Happy path: `verifyAuth` returns success with Bearer token from `WPCOM_TOKEN`
- Happy path: `apiGet` fetches successfully on first try
- Edge case: `apiGet` retries on 429, succeeds on 3rd attempt
- Edge case: `apiGet` fails all 3 retries, throws with last error
- Edge case: Auth fallback chain — `WPCOM_TOKEN` missing, falls back to `WP_APP_USER`+`WP_APP_PASS`
- Edge case: Lock file exists but is stale (>TTL), acquires anyway
- Edge case: Lock file exists and is fresh, throws LockError
- Error path: `verifyAuth` with no credentials returns descriptive error
- Error path: `apiPost` with network failure retries with backoff
- Happy path: `createBackup` writes JSON, `loadBackup` reads it back
- Happy path: `saveState`/`loadState` round-trip with processed/failed arrays

**Verification:**
- All tests pass
- Auth works with `WPCOM_TOKEN` env var against yololab.net (manual test)

---

- [ ] **Unit 2: Image ALT Module Wrapper**

**Goal:** Wrap `image-alt-text-optimizer.js` as an importable module that the skill can invoke.

**Requirements:** R5 (Image ALT), R14 (rollback)

**Dependencies:** Unit 1 (shared utilities)

**Files:**
- Create: `scripts/modules/image-alt.js`
- Modify: `scripts/image-alt-text-optimizer.js` (export core functions, replace hardcoded config with parameters)
- Test: `test/modules/image-alt.test.js`

**Approach:**
- Refactor `image-alt-text-optimizer.js` to export its phase functions: `phaseScan(config, options)`, `phaseFeatured(config, options)`, `phaseInline(config, options)`, `phaseReport(config)`, `phaseRollback(config, target)`
- Replace hardcoded `SITE_ID`, `SITE_DOMAIN`, `API_V2`, `API_DIRECT` with `config.siteId`, `config.domain`, etc.
- Replace internal auth/fetch with imports from `seo-shared.js`
- The module wrapper (`scripts/modules/image-alt.js`) is a thin adapter: loads config, calls the right phase function, returns structured result
- Keep the existing `main()` function for backward compatibility (CLI direct invocation) but have it delegate to the exported functions

**Patterns to follow:**
- Existing phase dispatch in `image-alt-text-optimizer.js` main()
- Module export pattern from `.claude/lib/proposal-engine.js`

**Test scenarios:**
- Happy path: `phaseScan` with sample=10 returns audit report with article count and image stats
- Happy path: `phaseFeatured` with dry-run returns list of proposed changes without writes
- Edge case: `phaseScan` with no articles returns empty report
- Edge case: `phaseFeatured` with `--resume` skips already-processed articles
- Error path: `phaseScan` with invalid auth returns auth error
- Integration: `phaseFeatured` creates backup file before any writes
- Integration: `phaseRollback("featured")` restores from backup

**Verification:**
- Module can be imported and called with config object
- CLI direct invocation still works (backward compatibility)
- Existing `npm run optimize:scan-sample` still functions

---

- [ ] **Unit 3: Meta Tags + Schema Module Wrappers**

**Goal:** Create module wrappers for meta-tags and schema-markup by combining the phase4 generator and applier scripts. Add backup/rollback that these scripts currently lack.

**Requirements:** R6 (Meta Tags), R7 (Schema Markup), R14 (rollback)

**Dependencies:** Unit 1 (shared utilities)

**Files:**
- Create: `scripts/modules/meta-tags.js`
- Create: `scripts/modules/schema-markup.js`
- Modify: `scripts/phase4-complete-seo-batch-generator.js` (export generation functions)
- Modify: `scripts/phase4-apply-seo-to-wordpress.js` (export application functions, add backup)
- Test: `test/modules/meta-tags.test.js`
- Test: `test/modules/schema-markup.test.js`

**Approach:**
- Export from `phase4-complete-seo-batch-generator.js`: `generateMetaOptimization(article)`, `generateSchemaMarkup(article)`, `generateOGTags(article)`
- Export from `phase4-apply-seo-to-wordpress.js`: `buildMetadataUpdate(postId, seoData)`, `updatePostMetadata(postId, config, metadata)`
- **Add backup before apply:** Before writing meta fields, fetch current values of `_yoast_wpseo_title`, `_yoast_wpseo_metadesc`, `_yoast_wpseo_schema` and save to backup JSON
- **Add rollback:** Read backup, re-apply original values via same API endpoint
- **Add auth verification:** Before first write, verify that `WPCOM_TOKEN` can write to `_yoast_wpseo_*` fields. If Yoast fields are rejected, surface error immediately instead of failing silently per-article
- Replace hardcoded `BLOG_ID` with config parameter
- Replace direct `fetch` calls with shared `apiGet`/`apiPost`
- Meta-tags module: scan → generate → apply (with backup) → verify → report
- Schema module: scan → generate → apply (with backup) → verify → report

**Patterns to follow:**
- Backup pattern from `image-alt-text-optimizer.js` lines 700-791
- Retry pattern from shared utilities (Unit 1)

**Test scenarios:**
- Happy path: Meta-tags module generates title + description for a sample article
- Happy path: Schema module generates JSON-LD for a sample article
- Happy path: Apply writes metadata and backup file contains original values
- Edge case: Article already has optimized meta title — skip, don't overwrite
- Edge case: Yoast fields not supported — module returns clear error before batch starts
- Error path: Apply fails mid-batch — partial backup exists, processed articles tracked in state
- Integration: Rollback restores original Yoast field values from backup
- Integration: Generate → apply → rollback round-trip preserves original data

**Verification:**
- `meta-tags` and `schema-markup` no longer throw "coming soon" errors in site-optimizer.js
- Backup files created before writes
- Rollback restores original meta field values
- Auth verification catches unsupported Yoast fields before batch starts

---

- [ ] **Unit 4: Internal Links Module Wrapper**

**Goal:** Wrap `internal-linker-v2.js` as a module and add the missing backup/rollback capability.

**Requirements:** R8 (Internal Links), R14 (rollback)

**Dependencies:** Unit 1 (shared utilities)

**Files:**
- Create: `scripts/modules/internal-links.js`
- Modify: `scripts/internal-linker-v2.js` (export core functions, add backup)
- Test: `test/modules/internal-links.test.js`

**Approach:**
- Export from `internal-linker-v2.js`: `fetchMap(config)`, `generateProposals(config)`, `injectLinks(config, options)`, `fixBrokenLinks(config)`
- **Add backup before injection:** Before modifying `post.content`, save `{ postId, originalContent }` to `seo-optimization-output/internal-links-backup.json`. This will be large (~50-100MB for full site) but is necessary for safe rollback
- **Add rollback function:** Read backup, re-apply original content via `POST /posts/{id}` with `{ content: originalContent }`
- Replace hardcoded `SITE_ID` with config parameter
- Replace internal auth/fetch with shared utilities
- Replace internal `data/tier1-articles.json` path with configurable data directory

**Patterns to follow:**
- Backup pattern from `image-alt-text-optimizer.js`
- Export pattern from Unit 2

**Test scenarios:**
- Happy path: `fetchMap` builds article mapping from tier1 data
- Happy path: `generateProposals` returns link proposals without modifying posts
- Happy path: `injectLinks` with dry-run shows proposed changes
- Edge case: Article already has "延伸閱讀" section — skip injection
- Edge case: Backup file grows large — verify JSON write/read handles >50MB
- Error path: Injection fails mid-batch — partial backup exists
- Integration: Inject → rollback round-trip restores original post content exactly
- Integration: Rollback preserves Gutenberg block comments in restored content

**Verification:**
- Rollback restores exact original `post.content` including Gutenberg block comments
- Dry-run mode shows changes without writing
- Large backup file (~50MB) reads/writes correctly

---

- [ ] **Unit 5: SEO Orchestrator Skill**

**Goal:** Create the `/seo` skill prompt and orchestrator state management. This is the conversational entry point that replaces `site-optimizer.js`.

**Requirements:** R1 (single entry), R2 (conversational mode), R15 (no module hard deps), R19 (structured reports)

**Dependencies:** Units 1-4 (all modules ready)

**Files:**
- Create: `.claude/skills/seo-orchestrator.md` (skill prompt template)
- Create: `scripts/lib/seo-orchestrator-state.js` (state persistence for cross-session resume)
- Modify: `.claude/skills/site-optimizer-config.json` (update module registry, mark old types as replaced)
- Test: `test/seo-orchestrator-state.test.js`

**Approach:**
- The skill prompt (`.claude/skills/seo-orchestrator.md`) is a markdown file that instructs Claude how to:
  1. Check for existing orchestrator state (resume detection)
  2. Run quick audit: load cached scan results or sample 100 articles
  3. Present findings as a consultant: coverage % per module, top recommendations
  4. Accept user direction (specific module or "do everything")
  5. Show confirmation before batch writes: article count, estimated time, cost estimate, 3 sample changes, backup status
  6. Execute by calling module scripts via Bash tool
  7. Report results per module
  8. Offer rollback if needed
- Orchestrator state (`seo-orchestrator-state.json`): `{ activeModule, batchId, startTime, articlesProcessed, articlesRemaining, userIntent, lastUpdated }`
- Quick audit cache (`seo-optimization-output/audit-cache.json`): `{ timestamp, modules: { imageAlt: { total, missing, weak }, metaTags: {...}, schema: {...}, links: {...} } }`
- Global lock managed at skill level — acquire before any module execution, release after
- Module execution is sequential (shared API rate limit), not parallel

**Patterns to follow:**
- Skill prompt structure from `.claude/skills/SITE-OPTIMIZER.md`
- Config structure from `.claude/skills/site-optimizer-config.json`

**Test scenarios:**
- Happy path: State file saves/loads correctly with all fields
- Happy path: State file detects interrupted batch on skill entry
- Edge case: State file is stale (>24h) — treat as abandoned, offer fresh start
- Edge case: No cached audit exists — triggers sample scan
- Edge case: Cached audit is >7 days old — triggers fresh sample scan
- Error path: Lock file exists — refuses to start, shows who holds the lock

**Verification:**
- `/seo` triggers the skill and presents audit findings
- Module execution via Bash tool works end-to-end
- Cross-session resume works: start batch → close Claude → reopen → resume offered
- Lock prevents concurrent execution

---

- [ ] **Unit 6: Script Deprecation and Cleanup**

**Goal:** Move superseded scripts to `scripts/_deprecated/`, update npm scripts, and clean up stale references.

**Requirements:** R21 (deprecation plan)

**Dependencies:** Unit 5 (skill functional, confirming scripts are truly superseded)

**Files:**
- Create: `scripts/_deprecated/` (directory for deprecated scripts)
- Modify: `package.json` (update npm scripts to use new module paths)
- Modify: `.claude/skills/SITE-OPTIMIZER.md` (mark as superseded by `/seo`)
- Modify: `.claude/lib/site-optimizer-command.js` (redirect to `/seo` or deprecate)

**Approach:**
- Move superseded scripts to `scripts/_deprecated/` in a single commit. The 4 core scripts to preserve (imported by module wrappers) are: (1) `image-alt-text-optimizer.js`, (2) `internal-linker-v2.js`, (3) `phase4-complete-seo-batch-generator.js`, (4) `phase4-apply-seo-to-wordpress.js`. All other SEO-related scripts in `scripts/` are candidates for deprecation
- Scripts to deprecate: all `phase3-*`, `phase-5-8-*`, `phase9-12-*`, `phase-13-16-*`, `phase17-20-*`, `phase-21-27-*`, versioned iterations (`seo-optimizer-v1/v2/v3`, `wp-seo-batch-v2/v3`), automation wrappers, demo scripts, MCP variants, Python/PHP variants
- Update `package.json` npm scripts: point `optimize:*` commands to new module wrappers
- Add deprecation note to `SITE-OPTIMIZER.md`: "Superseded by `/seo` skill. See `.claude/skills/seo-orchestrator.md`"
- The `_` prefix in `_deprecated` ensures clausidian ignores the directory (per `.gitignore` patterns)

**Test expectation:** none — pure file moves and config updates

**Verification:**
- `npm run optimize:scan-sample` still works (now via module wrapper)
- No imports reference moved files
- `scripts/` directory is clean: only core scripts, `lib/`, `modules/`, and `_deprecated/`

## System-Wide Impact

- **Interaction graph:** `/seo` skill → Bash tool → module scripts → WordPress REST API. No callbacks, middleware, or observers affected.
- **Error propagation:** Module errors bubble up as script exit codes. The skill prompt interprets non-zero exit as failure and reports to user. No silent failures.
- **State lifecycle risks:** Orchestrator state file could become stale if Claude crashes mid-execution. Mitigated by: 8-hour lock TTL, state file timestamp check, explicit "abandon" option.
- **API surface parity:** The existing `npm run optimize:*` scripts continue to work via module wrappers. No breaking change to CLI usage.
- **Unchanged invariants:** `image-alt-text-optimizer.js` and `internal-linker-v2.js` remain directly executable via CLI. Module wrappers are additive.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Yoast SEO fields may become unsupported on yololab's WP.com plan | Unit 3 includes auth verification step before first batch write. If fields are rejected, surface clear error before committing |
| Large backup files for internal-links (~50-100MB) | Monitor disk usage; add cleanup for backups >30 days old |
| image-alt refactoring breaks existing CLI usage | Keep `main()` function as backward-compatible CLI entry; module wrapper calls exported functions |
| WordPress.com API rate limits change | Rate limit config is parameterized in shared utils, not hardcoded. Easy to adjust |
| Long batches (6-8h) span multiple Claude sessions | Orchestrator state file enables resume; lock file prevents concurrent runs |
| 51 scripts moved to `_deprecated/` may break unknown references | Grep for script names before moving; the `_deprecated` directory preserves files (not deleted) |

## Documentation / Operational Notes

- Update `CLAUDE.md` to reference `/seo` as the primary SEO command
- Update `.claude/skills/SITE-OPTIMIZER.md` with deprecation notice
- The `site-optimizer-config.json` remains as the source of truth for site configurations

## Sources & References

- **Origin document:** [docs/brainstorms/2026-04-12-seo-orchestrator-skill-requirements.md](docs/brainstorms/2026-04-12-seo-orchestrator-skill-requirements.md)
- Related code: `scripts/image-alt-text-optimizer.js`, `scripts/internal-linker-v2.js`, `scripts/phase4-complete-seo-batch-generator.js`, `scripts/phase4-apply-seo-to-wordpress.js`
- Related learning: `docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md`
- Config: `.claude/skills/site-optimizer-config.json`
