---
title: "feat: Unify knowledge systems — Obsidian as canonical store"
type: feat
status: active
date: 2026-03-30
origin: docs/brainstorms/2026-03-30-knowledge-unification-requirements.md
---

# feat: Unify knowledge systems — Obsidian as canonical store

## Overview

Consolidate three parallel knowledge systems (auto-memory, claude-mem, Obsidian vault) into a unified architecture where Obsidian is the canonical store, auto-memory is pointer-only, behavioral rules live in CLAUDE.md, and claude-mem is a read-heavy search complement fed by an in-session bridge command.

## Problem Frame

Knowledge is scattered across auto-memory (7 files, project-scoped, auto-loaded), claude-mem (MCP database, cross-project), and Obsidian vault (PARA structure, human-readable). Finding prior knowledge requires knowing which system holds it. Duplicate content drifts out of sync. (see origin: docs/brainstorms/2026-03-30-knowledge-unification-requirements.md)

## Requirements Trace

- R1. Obsidian = canonical store for all durable knowledge
- R2. auto-memory migrated; MEMORY.md pointer-only; ongoing regeneration managed via CLAUDE.md routing instructions
- R3. claude-mem as read-heavy complement with cross-session timeline/search
- R4. Routing rules as conventions in CLAUDE.md, not enforced constraints
- R5. Durable knowledge routes to Obsidian via obsidian-agent
- R6. Critical behavioral rules promoted to CLAUDE.md for auto-loading
- R6b. MEMORY.md pointers designed so Claude knows to read referenced vault files when topics arise
- R7/R9. In-session bridge command syncs significant Obsidian writes to claude-mem
- R8. MEMORY.md entries reference vault notes, not duplicate content
- R10. _(merged into R8 and Success Criteria — see origin doc)_
- R11. All 7 existing auto-memory files migrated (7, not 6 — `feedback_benchmark_first.md` discovered during research)
- R12. claude-mem duplicate observations identified for manual review

## Scope Boundaries

- NOT redesigning obsidian-agent core or PARA structure
- NOT building new MCP servers
- NOT disabling Claude Code's auto-memory (managed, not blocked)
- NOT addressing plugin overhead (deferred)
- Slash commands are prompt templates, not scripts (see origin: feedback_architecture.md)

## Context & Research

### Relevant Code and Patterns

- **Bridge commands** (`.claude/commands/bridge-compound.md`, `bridge-plan.md`): Multi-step prompt templates that read source docs, extract structured data, create vault notes via obsidian-agent. New `/bridge-mem` follows this pattern.
- **Session-stop wrapper** (`scripts/session-stop-wrapper.sh`): Pure bash, reads stdin JSON, patches journal. Cannot be extended for claude-mem (no MCP access post-session).
- **CLAUDE.md structure**: Global (~33 lines) already has context hygiene, subagent rules. Project (~23 lines) has agent rules, CE paths. Room for ~15-20 lines of condensed behavioral rules in project CLAUDE.md.
- **Auto-memory schema**: Files use session-wrap frontmatter (`name`, `description`, `type`, `updated`, `expires`, `platform`). MEMORY.md is plain markdown index with `[Title](file.md)` links.
- **obsidian-agent CLI**: `note`, `patch`, `update`, `search`, `read`, `sync`, `--json` flag. All commands auto-handle frontmatter and index updates.

### Institutional Learnings

- Stop hooks cannot invoke Claude reasoning (docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md)
- `~/.claude/` has no git — rollback via `.bak` files for global config
- Wrapper-first validation: test in bash wrapper before upstreaming to CLI

## Key Technical Decisions

- **Behavioral rules → project CLAUDE.md (not global)**: Global CLAUDE.md already has context hygiene rules. Architecture-specific rules (stop hook limits, slash command nature) go in project CLAUDE.md to avoid affecting other projects. Rationale: project CLAUDE.md is git-tracked and project-scoped.
- **MEMORY.md pointer pattern**: One-line entries with enough context for Claude to know WHAT exists and WHERE to look. Format: `- [Title](vault-relative-path) — one-line description`. Claude won't auto-read vault files, but will proactively read them when the topic arises in conversation. This is acceptable because behavioral rules are in CLAUDE.md (always loaded) and vault content is for deep reference, not session-critical context.
- **In-session `/bridge-mem` slash command**: Follows bridge-compound pattern. Reads recent vault changes (via `obsidian-agent search` or journal), extracts observation summaries, calls claude-mem MCP tools. Runs within active session where MCP tools are available. Rationale: stop hooks can't access MCP; per-write hooks too noisy; manual command gives user control over when to sync.
- **Migration with backup**: Copy all memory/ files to `memory-backup-YYYY-MM-DD/` before migration. Project CLAUDE.md changes are git-tracked. Global CLAUDE.md gets `.bak` copy.
- **Auto-memory regeneration management**: Add explicit routing instructions to project CLAUDE.md telling Claude to route new knowledge to Obsidian instead of creating auto-memory content files. This is a convention, not enforcement — but with clear instructions in CLAUDE.md, Claude will follow them from turn 1.

## Open Questions

### Resolved During Planning

- **Which CLAUDE.md for behavioral rules?** → Project CLAUDE.md. Global already covers context hygiene. Architecture lessons are project-specific. Project CLAUDE.md is git-tracked for rollback.
- **MEMORY.md pointer behavior**: Claude won't auto-follow vault paths, but this is acceptable. Behavioral rules (the critical ones) are in CLAUDE.md. MEMORY.md pointers serve as a directory for Claude to look up when topics arise. Verified: current `[Title](file.md)` format works for co-located files; vault pointers need absolute or vault-relative paths.
- **Migration mapping for 7 files**: See Unit 3 for detailed per-file routing.
- **7 files, not 6**: Research discovered `feedback_benchmark_first.md` (benchmark before planning rule). Origin doc said 6; actual count is 7.

### Deferred to Implementation

- Exact wording of CLAUDE.md behavioral rules section — depends on reviewing the condensed content against what's already there
- Whether `/bridge-mem` should auto-detect recent changes or require explicit arguments — try simplest approach (auto-detect via journal/git) first
- claude-mem observation format — depends on what fields claude-mem's MCP tools accept

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```mermaid
graph TD
    subgraph "Session Start (Auto-loaded)"
        A[Global CLAUDE.md] --> C[Claude Context]
        B[Project CLAUDE.md<br/>+ behavioral rules<br/>+ routing instructions] --> C
        D[MEMORY.md<br/>pointer-only index] --> C
    end

    subgraph "During Session (On-demand)"
        C -->|topic arises| E[Read Obsidian vault note]
        C -->|search needed| F[claude-mem smart_search]
        C -->|search needed| G[obsidian-agent search]
    end

    subgraph "Knowledge Routing (Convention)"
        H[New durable knowledge] -->|routing rule in CLAUDE.md| I[obsidian-agent note/patch]
        H -->|NOT| J[auto-memory content files]
    end

    subgraph "Bridge (Manual trigger)"
        K[/bridge-mem command] -->|reads recent vault changes| L[Extract observations]
        L -->|claude-mem MCP tools| M[claude-mem database]
    end
```

## Implementation Units

- [ ] **Unit 1: Backup auto-memory files**

**Goal:** Create safety net before any migration changes.

**Requirements:** R11 (migration rollback)

**Dependencies:** None

**Files:**
- Read: `~/.claude/projects/C--DEX-data-Claude-Code-DEV/memory/*`
- Create: `~/.claude/projects/C--DEX-data-Claude-Code-DEV/memory-backup-2026-03-30/` (copy of all files)
- Read: `~/.claude/CLAUDE.md` (backup as `~/.claude/CLAUDE.md.bak`)

**Approach:**
- Copy entire memory/ directory to memory-backup-2026-03-30/
- Copy global CLAUDE.md to CLAUDE.md.bak
- Verify backup completeness (file count matches)

**Patterns to follow:**
- Institutional learning: `~/.claude/` has no git — `.bak` for rollback

**Test scenarios:**
- Happy path: All 8 files (MEMORY.md + 7 content) copied to backup dir
- Happy path: Global CLAUDE.md.bak created
- Edge case: Backup dir already exists → skip or warn, don't overwrite

**Verification:**
- `memory-backup-2026-03-30/` contains exact copies of all files
- `~/.claude/CLAUDE.md.bak` exists and matches original

---

- [ ] **Unit 2: Promote behavioral rules to project CLAUDE.md**

**Goal:** Ensure critical behavioral guardrails are auto-loaded from turn 1, independent of auto-memory files.

**Requirements:** R6, R4

**Dependencies:** Unit 1 (backup exists)

**Files:**
- Modify: `C:/DEX_data/Claude Code DEV/CLAUDE.md` (project)
- Read: `~/.claude/projects/C--DEX-data-Claude-Code-DEV/memory/feedback_architecture.md`
- Read: `~/.claude/projects/C--DEX-data-Claude-Code-DEV/memory/feedback_context_hygiene.md`
- Read: `~/.claude/projects/C--DEX-data-Claude-Code-DEV/memory/feedback_benchmark_first.md`
- Read: `~/.claude/CLAUDE.md` (global, to check for overlap)

**Approach:**
- Read all 3 feedback files and global CLAUDE.md
- Identify rules NOT already in global CLAUDE.md (avoid duplication)
- Condense unique rules into ~15-20 lines as a new `## Behavioral Rules` section in project CLAUDE.md
- Include routing instructions telling Claude to route new knowledge to Obsidian, not auto-memory content files
- Key rules to promote: stop hooks can't use Claude, ~/.claude/ has no git, slash commands are prompts, plugin overhead ~10-15K, benchmark before planning local LLM

**Patterns to follow:**
- Project CLAUDE.md's existing concise bullet style
- Global CLAUDE.md's context hygiene section format

**Test scenarios:**
- Happy path: Project CLAUDE.md gains `## Behavioral Rules` section with condensed rules
- Happy path: No duplication with global CLAUDE.md's existing context hygiene rules
- Edge case: Project CLAUDE.md total length stays under ~50 lines (was ~23, adding ~15-20)
- Integration: New session loads both CLAUDE.md files → all behavioral rules visible from turn 1

**Verification:**
- Project CLAUDE.md contains all critical behavioral rules from the 3 feedback files
- No rule duplicated between global and project CLAUDE.md
- Combined CLAUDE.md load is under ~80 lines total (~33 global + ~45 project)

---

- [ ] **Unit 3: Migrate durable knowledge to Obsidian vault**

**Goal:** Create Obsidian notes for all auto-memory content that qualifies as durable knowledge.

**Requirements:** R1, R5, R11

**Dependencies:** Unit 2 (behavioral rules already promoted to CLAUDE.md)

**Files:**
- Read: All 7 auto-memory content files
- Create (via obsidian-agent): Vault notes for durable knowledge
- Reference: `CONVENTIONS.md` for vault note schema

**Approach — per-file routing:**

| Auto-memory file | Destination | Vault note type | Rationale |
|---|---|---|---|
| `user_profile.md` | CLAUDE.md pointer only | N/A | Identity info (language, style) already in global CLAUDE.md. One-line pointer suffices |
| `project_dev-vault.md` | `projects/dev-vault-status.md` | project | Active project status = vault project note |
| `feedback_architecture.md` | `resources/architecture-lessons.md` | resource (subtype: learning) | Durable knowledge. Rules already promoted to CLAUDE.md in Unit 2 |
| `feedback_context_hygiene.md` | `resources/context-engineering-hygiene.md` | resource (subtype: learning) | Durable knowledge. Rules already promoted to CLAUDE.md in Unit 2 |
| `feedback_benchmark_first.md` | `resources/benchmark-first-rule.md` | resource (subtype: learning) | Durable knowledge. Rule already promoted to CLAUDE.md in Unit 2 |
| `reference_tools.md` | `resources/toolchain-reference.md` | resource (subtype: reference) | Reference knowledge |
| `reference_claude_agent_sdk_api.md` | `resources/claude-agent-sdk-api.md` | resource (subtype: reference) | Reference knowledge |

- Use `obsidian-agent note` to create each vault note with proper frontmatter
- Transfer content, adapting frontmatter from session-wrap schema to vault schema
- Run `obsidian-agent sync` after all notes created

**Patterns to follow:**
- Bridge-compound command's schema mapping logic (CE fields → vault fields)
- CONVENTIONS.md frontmatter schema (subtype, maturity, domain, tags, relation_map)
- Existing vault notes in `resources/` for format reference

**Test scenarios:**
- Happy path: 6 new vault notes created (user_profile has no vault note, just pointer)
- Happy path: Each note has valid frontmatter per CONVENTIONS.md
- Happy path: `obsidian-agent sync` succeeds, indices updated
- Edge case: Note with same title already exists → check and merge or skip
- Error path: obsidian-agent CLI failure → stop and report, don't continue with partial state

**Verification:**
- 6 new notes exist in vault at expected paths
- Each note appears in vault index (`_index.md`)
- Content matches source auto-memory files (no data loss)

---

- [ ] **Unit 4: Redesign MEMORY.md as pointer-only index**

**Goal:** Replace MEMORY.md with a lean pointer index referencing Obsidian notes and CLAUDE.md.

**Requirements:** R2, R6b, R8

**Dependencies:** Unit 3 (vault notes exist to point to)

**Files:**
- Modify: `~/.claude/projects/C--DEX-data-Claude-Code-DEV/memory/MEMORY.md`
- Delete: All 7 auto-memory content files (after backup verified in Unit 1)

**Approach:**
- Rewrite MEMORY.md as a lean index (under 10 entries, each under 150 chars)
- Format: `- [Title](vault-path-or-note) — one-line description`
- For behavioral rules: reference CLAUDE.md, not individual files
- For vault notes: use project-root-relative paths (e.g., `resources/architecture-lessons.md`) since the vault IS the project working directory. Claude resolves these relative to the working directory, not the memory/ directory
- Add a preamble comment in MEMORY.md: `<!-- Vault paths below are relative to the project root (C:/DEX_data/Claude Code DEV/) -->`
- Delete the 7 content files from memory/ directory
- Content is preserved in: Obsidian vault (Unit 3) + CLAUDE.md (Unit 2) + backup (Unit 1)

**Patterns to follow:**
- Current MEMORY.md format (markdown links with descriptions)
- Keep under 10 entries per success criteria

**Test scenarios:**
- Happy path: MEMORY.md has ~7 entries, all under 150 chars, pointing to vault notes or CLAUDE.md
- Happy path: All 7 content files removed from memory/ directory
- Edge case: Claude Code auto-regenerates a content file in a future session → routing rules in CLAUDE.md should prevent this, but if it happens, the file won't conflict
- Integration: New session → MEMORY.md loads as text → Claude sees pointer index → when user asks about a topic, Claude reads the referenced vault note

**Verification:**
- MEMORY.md is under 10 entries
- No content files remain in memory/ (only MEMORY.md)
- Starting a new session, Claude can find any migrated knowledge within one query

## Deferred Units (Future Work)

> Units 5 and 6 were moved here after document review discovered that claude-mem's MCP server exposes **zero write tools** — all 6 tools (`smart_search`, `search`, `timeline`, `get_observations`, `smart_outline`, `smart_unfold`) are read-only. Unit 5 (`/bridge-mem`) is architecturally impossible with the current claude-mem MCP surface. Unit 6 (audit) is decouplable cleanup with no downstream dependency.
>
> **R7/R9 (bridge) and R12 (audit) are deferred** until claude-mem adds write capabilities or an alternative bridging mechanism is identified. The core migration (Units 1-4) is independently shippable and addresses R1-R6b, R8, R11.

- **Unit 5 (deferred): /bridge-mem slash command** — Blocked: claude-mem has no write MCP tools. Revisit when claude-mem adds `create_observation` or equivalent, or explore claude-mem's HTTP API/database directly.
- **Unit 6 (deferred): claude-mem duplicate audit** — Not blocked but low priority. Can run anytime post-migration as a one-time manual review.

## System-Wide Impact

- **Interaction graph:** CLAUDE.md (auto-loaded) → Claude behavior; MEMORY.md (auto-loaded) → context pointers; obsidian-agent (CLI) → vault writes; claude-mem MCP (in-session) → search/timeline; session-stop hook (post-session) → journal only (unchanged)
- **Error propagation:** If obsidian-agent fails during migration, stop and report — partial state is recoverable via backup. If claude-mem bridge fails, it's non-critical — warn and continue. Auto-memory regeneration is a convention violation, not an error.
- **State lifecycle risks:** Auto-memory content files may be regenerated by Claude Code in future sessions despite routing rules. This is managed, not prevented. The routing instructions in CLAUDE.md should minimize this, but occasional regeneration is expected and acceptable.
- **API surface parity:** session-wrap skill also writes to auto-memory — it may need awareness of the new routing rules. Add a note in CLAUDE.md about session-wrap behavior.
- **Unchanged invariants:** obsidian-agent CLI, vault PARA structure, frontmatter schema, session-stop hook journal logging, claude-mem MCP tool interfaces — all unchanged. This plan only changes what content goes where, not how the tools work.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| MEMORY.md pointers don't trigger Claude to read vault files | Acceptable: behavioral rules are in CLAUDE.md (always loaded). Vault pointers are for deep reference, not session-critical. Claude will read when topic arises in conversation |
| Auto-memory regenerates content files | Routing instructions in CLAUDE.md minimize this. Occasional regeneration is acceptable — it doesn't break the system, just adds noise that next session can clean |
| claude-mem has no write MCP tools | Units 5-6 deferred. claude-mem continues as read-only complement. Bridge revisited when write tools are available |
| CLAUDE.md becomes too long | Budget: ~50 lines project CLAUDE.md (was 23, adding ~20-25). Combined ~83 lines total. Still compact. Monitor with `/improve` |
| Migration loses content | Backup in Unit 1. Project CLAUDE.md is git-tracked. Vault notes are git-tracked. Only global CLAUDE.md.bak is untracked |
| session-wrap skill writes auto-memory content | Add note in routing rules section of CLAUDE.md that session-wrap should respect Obsidian-first routing |

## Documentation / Operational Notes

- Update project CLAUDE.md with behavioral rules and routing instructions (Unit 2)
- Consider adding migration notes to `docs/solutions/` via `/ce:compound` after completion
- `/improve` cycle should monitor MEMORY.md entry count and CLAUDE.md length

## Sources & References

- **Origin document:** [docs/brainstorms/2026-03-30-knowledge-unification-requirements.md](docs/brainstorms/2026-03-30-knowledge-unification-requirements.md)
- Related learnings: `docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md`
- Related plan: `docs/plans/2026-03-29-004-refactor-vault-knowledge-framework-plan.md` (completed, provides vault schema)
- Bridge pattern: `.claude/commands/bridge-compound.md`, `.claude/commands/bridge-plan.md`
- Auto-memory: `~/.claude/projects/C--DEX-data-Claude-Code-DEV/memory/`
- CLAUDE.md: `~/.claude/CLAUDE.md` (global), `C:/DEX_data/Claude Code DEV/CLAUDE.md` (project)
