---
title: "refactor: Optimize Claude Code AI Workflow — Breakage Fixes, Token Efficiency, and Context Intelligence"
type: refactor
status: complete
date: 2026-04-06
---

# refactor: Optimize Claude Code AI Workflow

## Overview

This plan addresses 10 identified issues across the Claude Code + AI workflow stack: active breakages that silently fail, hook configurations that waste tokens or add cold-start latency, missing automated context pressure signals, documentation drift between CLAUDE.md and actual config, cross-platform script bugs, dead code, and an ambiguous research pipeline dependency state.

The work is entirely configuration-layer — no Python core or watermark system changes.

## Problem Frame

A repo-research pass (2026-04-06) surfaced a cluster of fixable issues in the `.claude/` config layer. Several are active failures (Ollama MCP silently broken, research pipeline running degraded). Others are silent costs accumulated over time: a `prompt`-type hook fires a Claude model call on every `git commit`; `npx` cold-starts on every JS/TS save; the main project has no automated context pressure signal even though a more mature implementation exists in a sub-tool. Documentation has drifted from reality.

## Requirements Trace

- R1. Ollama local LLM MCP server must start successfully
- R2. `proposal-engine.js` must reference a currently valid model ID
- R3. Git commit workflow must not consume Claude API tokens for format checking
- R4. JS/TS formatting hook must not add cold-start latency from `npx`
- R5. Main project must have automated context pressure signals (not just CLAUDE.md text rules)
- R6. CLAUDE.md MCP Servers table must reflect actual `.mcp.json` state
- R7. `.claude/commands/` frontmatter must have accurate metadata for `/improve` signal detection
- R8. `research-status.md` bash commands must run correctly under Git Bash
- R9. Dead `@octokit/rest` dependency must be removed
- R10. Research pipeline's MCP dependency state must be explicitly documented

## Scope Boundaries

- Does not change the Python watermark removal system
- Does not implement new features in the research pipeline — only clarifies its dependency state
- Does not migrate `github-api.js` to use `@octokit/rest` (that is a separate refactor, larger scope)
- Does not promote all hooks from `claude-session-manager-new` — only the two with clear, low-noise value

## Context & Research

### Relevant Code and Patterns

- Active git commit hook (prompt type, token-consuming): `~/.claude/settings.json` lines 59–69
- npx prettier hook: `~/.claude/settings.json` lines 82–89
- Broken Ollama path: `.claude/settings.local.json` line 5 (`projects/tools/` → missing `_` prefix)
- Old model ID: `.claude/lib/proposal-engine.js` line 56 (`claude-opus-4-1`)
- Promoted hook source (context-guard): `projects/_tools/claude-session-manager-new/.claude/hooks/context-guard.sh`
- Promoted hook source (cost-tracker): `projects/_tools/claude-session-manager-new/.claude/hooks/cost-tracker.sh`
- Windows path bug: `.claude/commands/research-status.md` line 63
- Dead dependency: `.claude/package.json` → `@octokit/rest`
- Research pipeline config: `projects/_tools/research-pipeline/config.py`
- CLAUDE.md MCP table: `CLAUDE.md` (MCP Servers section)
- Command frontmatter: `.claude/commands/*.md` (14 files, all `title: "Untitled"`)

### Institutional Learnings

- **Session-stop wrapper pattern** (`docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md`): Hook array ordering is guaranteed; bash wrapper + jq stdin extraction is stable on Windows Git Bash
- **Context engineering strategy** (`docs/plans/2026-03-29-003-feat-context-engineering-strategy-plan.md`): 12 active plugins consume ~35–46K fixed tokens; effective budget is below 75% of context limit; `/compact` at natural boundaries; subagents for >50K output
- **Workflow self-iteration** (`docs/plans/2026-03-29-001-feat-workflow-self-iteration-plan.md`): `~/.claude/` is NOT a git repo — always back up to `.bak` before modifying; risk stratification: global config = high risk
- **Local LLM infrastructure** (`docs/plans/2026-03-29-005-feat-local-llm-infrastructure-plan.md`): OllamaClaude MCP should remain project-level only; do NOT set `ANTHROPIC_BASE_URL` to route through local proxy

### External References

Not needed — all patterns are established in the local codebase and institutional learnings.

## Key Technical Decisions

- **Shell `command` hook over `prompt` hook for git commit**: A `command` hook uses zero tokens and sub-millisecond execution. The conventional commit format is already mandated in both CLAUDE.md files — the check is redundant as a Claude call.
- **`node_modules/.bin/prettier` over `npx`**: Prettier is a devDependency in `.claude/package.json`. Using the local binary eliminates npm registry lookup and package resolution on every JS/TS save. Path: `.claude/node_modules/.bin/prettier`.
- **Promote only `context-guard.sh` and `cost-tracker.sh`**: These two hooks solve a clear gap (automated context pressure signal, JSONL cost tracking). The other hooks in `claude-session-manager-new` (`quality-gate`, `validate-sdd-context`, `sop-compact-reminder`) are tied to that sub-project's SOP pipeline and would add noise in the main project.
- **Research pipeline → document WebSearch-only posture**: Enabling arxiv/huggingface/agent-memory MCP servers for periodic pipeline runs has higher maintenance cost than the benefit. Document the current WebSearch fallback as the intended mode and update `config.py` to remove the MCP server name references.
- **Do not merge `github-api.js` into `@octokit/rest` now**: Removing the dead dependency is the minimal correct action. A full migration is a separate work item.

## Open Questions

### Resolved During Planning

- **Should context-guard be global or project-level?** Global — context pressure signals are useful across all projects. The hook must be written to be silent when context is healthy.
- **Which model should replace `claude-opus-4-1`?** `claude-opus-4-6` — the latest Opus per the environment context (2026-04-06). The proposal engine runs on-demand analysis where quality matters.
- **Should cost-tracker output go to stdout (visible in HUD) or a file?** File (`~/.claude/cost-log.jsonl`) — preserves session history across resets; HUD can optionally read it. Matches `claude-session-manager-new` pattern.

### Deferred to Implementation

- Whether to add a prettier global install as a fallback when `.claude/node_modules/.bin/prettier` is missing — check at implementation time whether `.claude/node_modules/` is populated.
- Exact transcript-size thresholds for context-guard warning levels — read the source in `context-guard.sh` and adapt as needed.
- Whether `research-status.md` line 63 path issue extends to other command files — check during Unit 4 pass.

## Implementation Units

- [x] **Unit 1: Active Breakage Repairs**

**Goal:** Fix the two silently broken configs — Ollama MCP wrong path and proposal-engine outdated model ID.

**Requirements:** R1, R2

**Dependencies:** None

**Files:**
- Modify: `.claude/settings.local.json`
- Modify: `.claude/lib/proposal-engine.js`

**Approach:**
- In `.claude/settings.local.json` line 5: change `projects/tools/local-llm/ollama-claude/index.js` → `projects/_tools/local-llm/ollama-claude/index.js`
- In `.claude/lib/proposal-engine.js` line 56: change `"claude-opus-4-1"` → `"claude-opus-4-6"`

**Patterns to follow:**
- `.mcp.json` uses `projects/_tools/` consistently; `.claude/settings.local.json` was an outlier

**Test scenarios:**
- Happy path: Start a new Claude Code session → Claude Code server logs show `ollama-claude` MCP registered without "file not found" error
- Happy path: Call `generateProposals()` in proposal engine test → no `model_not_found` API error
- Edge case: `ANTHROPIC_API_KEY` not set → same `throw new Error(...)` behavior as before (model change must not alter error handling)

**Verification:**
- `.claude/settings.local.json` args array contains `projects/_tools/local-llm/ollama-claude/index.js`
- `proposal-engine.js` line 56 references `claude-opus-4-6`
- `npm run test:proposal` passes

---

- [x] **Unit 2: Hook Token Efficiency**

**Goal:** Eliminate Claude API token consumption from the git commit hook and remove `npx` cold-start from the JS/TS formatter hook.

**Requirements:** R3, R4

**Dependencies:** None (both changes are in `~/.claude/settings.json`)

**Files:**
- Modify: `~/.claude/settings.json`

**Approach:**
- Back up `~/.claude/settings.json` to `~/.claude/settings.json.bak` before editing
- **Git commit hook** (lines 59–69): Replace the `prompt`-type hook with a `command`-type hook that runs a shell grep check on the commit message. The check should exit 0 silently if valid, emit a warning message via echo if not. Do not block the commit — just warn. Suggested pattern: extract `last_user_message` from stdin via jq, grep for `^(feat|fix|refactor|docs|chore|test|perf|ci|build):`, print a reminder if it doesn't match.
- **npx prettier hook** (line 84): Replace `npx prettier --write "$f"` with `.claude/node_modules/.bin/prettier --write "$f" 2>/dev/null || npx prettier --write "$f" || true`. This tries local binary first, falls back to npx if not found, suppresses errors either way.
- Validate the full JSON with `python -m json.tool ~/.claude/settings.json` after editing

**Patterns to follow:**
- Other `command` hooks in the same settings file use `bash -c 'input=$(cat); ...'` pattern with `jq` stdin parsing
- `session-stop-wrapper.sh` shows the correct `jq -r ".last_user_message"` extraction pattern

**Test scenarios:**
- Happy path: `git commit -m "feat: add something"` → no Claude API call, no warning printed
- Error path: `git commit -m "add something"` → warning message printed to stderr, commit still proceeds (non-blocking)
- Happy path: Edit a `.js` file → prettier runs without npx cold-start (runs in <500ms vs previous ~2s)
- Edge case: `.claude/node_modules/.bin/prettier` absent → fallback to npx, no error surfaced to user

**Verification:**
- `python -m json.tool ~/.claude/settings.json` exits 0
- Committing a valid conventional message produces no extra round-trip in Claude Code transcript
- No `PostToolUse` hook with `type: "prompt"` remains for the Bash matcher

---

- [x] **Unit 3: Automated Context Intelligence Hooks**

**Goal:** Promote `context-guard.sh` and `cost-tracker.sh` from the sub-project into the main project's scripts and wire them into global settings hooks.

**Requirements:** R5

**Dependencies:** None

**Files:**
- Read source: `projects/_tools/claude-session-manager-new/.claude/hooks/context-guard.sh`
- Read source: `projects/_tools/claude-session-manager-new/.claude/hooks/cost-tracker.sh`
- Create: `scripts/context-guard.sh`
- Create: `scripts/cost-tracker.sh`
- Modify: `~/.claude/settings.json`

**Approach:**
- Copy (do not move) the two hook scripts to `scripts/` — keep originals in the sub-project
- Review each script before copying: strip any SOP-specific references (S0-S7 stage tracking, SDD context validation) that tie them to the sub-project pipeline
- **context-guard**: Should emit a one-line warning at three transcript-size thresholds (e.g., 60%, 75%, 90% of limit). The warning should include a suggested action (`/compact now`, `/clear`). Must be silent below the first threshold.
- **cost-tracker**: Should append a JSONL entry (`{"ts": ..., "tool": ..., "cost": ...}`) to `~/.claude/cost-log.jsonl` on each tool use. Entry format must be readable by `/local-cost` skill.
- Add both to `~/.claude/settings.json`:
  - `context-guard.sh`: PostToolUse hook (any tool), async: false, timeout: 5s
  - `cost-tracker.sh`: PostToolUse hook (any tool), async: true, timeout: 5s
- Back up settings.json to `.bak` before modifying; validate JSON after

**Patterns to follow:**
- All existing hooks in settings.json use `bash -c 'input=$(cat); ...'` with jq stdin parsing
- Async hooks in settings.json use `"async": true` on the hook object
- `session-stop-wrapper.sh` shows robust stdin reading pattern with fallbacks

**Test scenarios:**
- Happy path: Session with normal tool use → no warning messages, cost-log.jsonl appended with valid JSONL
- Happy path: Simulated large transcript (inject env var or test flag) → warning printed at threshold
- Edge case: `~/.claude/cost-log.jsonl` does not exist → cost-tracker creates it (not an error)
- Edge case: context-guard runs on a 10-tool session → silent, no false warnings
- Integration: `/local-cost` skill reads `~/.claude/cost-log.jsonl` → parses without error

**Verification:**
- Both scripts exist in `scripts/` and are executable (`chmod +x`)
- `~/.claude/settings.json` JSON is valid
- Manual session produces `~/.claude/cost-log.jsonl` entries after tool use
- No spurious warnings during normal-size sessions

---

- [x] **Unit 4: Documentation Hygiene and Script Portability**

**Goal:** Fix three documentation and portability issues: CLAUDE.md MCP table drift, stale command frontmatter, and Windows path in `research-status.md`.

**Requirements:** R6, R7, R8

**Dependencies:** None (pure documentation)

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/commands/research-status.md`
- Modify: `.claude/commands/*.md` (14 files — frontmatter only)

**Approach:**
- **CLAUDE.md MCP Servers table**: Replace the current table with a table that reflects actual `.mcp.json` state:
  - `wpcom-mcp` → active, WordPress.com, "SEO optimization, content publishing"
  - `arxiv` → disabled (WebSearch替代)
  - `huggingface` → disabled (SEO工作不需要)
  - `fetch` → disabled (WebFetch工具替代)
  - `agent-memory` → removed (not in `.mcp.json`)
  - Add note: "To re-enable, rename key from `_disabled_<name>` to `<name>` in `.mcp.json`"
- **`research-status.md`**: Find the `ls -la "C:\DEX_data\Claude Code DEV\..."` command (line ~63). Replace with the POSIX-style path: `ls -la "/c/DEX_data/Claude Code DEV/resources/research-scan-"*.md`. Check if any other commands in the same file use Windows-style backslash paths.
- **Command frontmatter**: For each of the 14 `.claude/commands/*.md` files, update:
  - `title`: Set to the command's actual purpose (e.g., `journal.md` → "Create or open today's journal entry")
  - `summary`: One sentence describing what the command does
  - `domain`: Match the command's actual domain (not all `knowledge-management`; e.g., `research.md` → `research`, `capture.md` → `knowledge-management`, `bridge-plan.md` → `planning`)
  - Do not change the command body content, only frontmatter

**Patterns to follow:**
- Existing command files use YAML frontmatter with `title`, `type`, `created`, `updated`, `status`, `maturity`, `domain`, `summary`
- AGENT.md § Manual Editing Rules for frontmatter field conventions
- Other bash scripts in `scripts/` use `/c/DEX_data/...` POSIX-style paths

**Test scenarios:**
- Happy path: Run `research-status` slash command in Git Bash context → `ls` command resolves correctly, no "No such file" error
- Happy path: Run `/improve` → reads command frontmatter, correctly identifies domain gaps (not all "knowledge-management" false positives)
- Edge case: Scan all 14 command files for remaining Windows backslash paths in bash code blocks

**Verification:**
- CLAUDE.md MCP table has 4 rows (1 active, 3 disabled), no `agent-memory` row
- `research-status.md` bash blocks contain no `C:\` backslash paths
- All 14 command files have non-empty `summary` and non-`"Untitled"` title

---

- [x] **Unit 5: Dead Dependency Removal**

**Goal:** Remove unused `@octokit/rest` from `.claude/package.json`.

**Requirements:** R9

**Dependencies:** None

**Files:**
- Modify: `.claude/package.json`
- Modify: `.claude/package-lock.json` (generated by npm)

**Approach:**
- Remove the `@octokit/rest` entry from `dependencies` in `.claude/package.json`
- Run `npm install` in the `.claude/` directory to regenerate `package-lock.json`
- Verify that `github-api.js` does not import `@octokit/rest` (it uses Node's built-in `https` module)

**Patterns to follow:**
- `.claude/package.json` is a minimal utility package; keep it lean

**Test scenarios:**
- Happy path: `npm install` in `.claude/` completes without error, no `@octokit/rest` in `node_modules/`
- Happy path: `npm run test:proposal` still passes (proposal engine does not use octokit)
- Error path: Grep `.claude/lib/` for `require('@octokit/rest')` → no matches (confirm it was truly unused)

**Verification:**
- `.claude/package.json` has no `@octokit/rest` entry
- `npm run test:proposal` passes
- `.claude/node_modules/@octokit/` does not exist

---

- [x] **Unit 6: Research Pipeline Dependency Clarification**

**Goal:** Officially document that the research pipeline runs in WebSearch-only mode and remove dead MCP server name references from its config.

**Requirements:** R10

**Dependencies:** Unit 4 (CLAUDE.md update context)

**Files:**
- Modify: `projects/_tools/research-pipeline/config.py`
- Modify: `CLAUDE.md` (Research Pipeline section, if present)

**Approach:**
- Read `config.py` and find where it references `arxiv`, `huggingface`, `fetch`, or `agent-memory` MCP server names
- Replace hard-coded MCP server names with a comment block documenting the WebSearch fallback posture: "These MCPs are disabled. Scanners fall back to WebSearch. To re-enable, update .mcp.json and this config."
- If `config.py` has a `MCP_SERVERS` dict or similar, convert it to a commented-out reference with the fallback note
- In CLAUDE.md, update the "MCP Servers" or "Research Pipeline" section to note that the research pipeline uses WebSearch fallbacks; arxiv/huggingface are disabled by choice

**Patterns to follow:**
- `.mcp.json` uses `_disabled_` prefix convention to mark disabled servers with explanatory comments — adopt the same spirit in `config.py`

**Test scenarios:**
- Happy path: Run the research pipeline scanner manually → it completes using WebSearch without MCP-related errors
- Edge case: `config.py` references a non-existent MCP server name → verify this is the only source of the silent degradation (no other config files reference the disabled MCPs)

**Verification:**
- `config.py` has no live references to `arxiv`, `huggingface`, `fetch`, `agent-memory` as active MCP dependencies
- CLAUDE.md accurately describes the pipeline's current WebSearch-only operating mode

## System-Wide Impact

- **Hook changes affect all Claude Code sessions globally** — `~/.claude/settings.json` is not project-scoped. Test in a simple throwaway session before finalizing Unit 2 and Unit 3 changes.
- **Error propagation**: All new `command` hooks must use `|| true` or explicit `exit 0` to avoid blocking Claude Code on hook failure. Silent failure is always preferable to a broken hook surfacing as a session error.
- **Unchanged invariants**: The `Stop` hook (session journal), `PreCompact` hook (vault snapshot), Python formatter hook, and vault sync hooks are not changed by this plan.
- **Integration coverage**: Unit 3 (cost-tracker) integrates with the `/local-cost` skill — verify the JSONL schema matches what the skill expects before finalizing.
- **API surface parity**: `proposal-engine.js` model update (Unit 1) must not change the function signature or output schema — only the underlying model call changes.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `~/.claude/settings.json` edit breaks hooks globally | Always back up to `.bak` first; validate JSON before saving; test in a fresh session |
| `context-guard.sh` emits false warnings during normal sessions | Set conservative thresholds (first warning at 60%+); make warnings dismissible/informational only, never blocking |
| `cost-tracker.sh` JSONL schema incompatible with `/local-cost` | Read `/local-cost` skill source before finalizing schema; match field names exactly |
| `npx` fallback in prettier hook still has cold-start | Acceptable — it only triggers when local binary is missing, which should be rare after `npm install` |
| Removing `@octokit/rest` breaks something not found by grep | Run full `npm run test:proposal` and `npm run test:proposal-integration` after removal |
| `config.py` research pipeline changes break scanner imports | Read the full `config.py` before editing; changes are documentation-only unless MCP names are used in import statements |

## Sources & References

- Related code: `.claude/settings.local.json`, `~/.claude/settings.json`, `.claude/lib/proposal-engine.js`
- Hook sources: `projects/_tools/claude-session-manager-new/.claude/hooks/`
- Institutional learnings: `docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md`
- Prior planning context: `docs/plans/2026-03-29-003-feat-context-engineering-strategy-plan.md`
- Prior planning context: `docs/plans/2026-03-29-005-feat-local-llm-infrastructure-plan.md`
