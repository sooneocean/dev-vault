---
date: 2026-03-30
topic: knowledge-unification
---

# Knowledge System Unification

## Problem Frame

The current toolchain runs three parallel knowledge systems that don't communicate:

1. **auto-memory** (`~/.claude/projects/*/memory/`) — file-based, project-scoped, auto-loaded at session start
2. **claude-mem** (MCP database) — cross-project, cross-session, searchable via `smart_search`/`timeline`
3. **Obsidian vault** (PARA structure) — managed by obsidian-agent, human-readable, indexed

Knowledge is scattered across these three systems. Finding prior knowledge requires knowing which system holds it. Some knowledge gets duplicated and drifts out of sync. New sessions lack unified context because each system only sees its own slice.

## Requirements

**Knowledge Architecture**

- R1. Obsidian vault is the canonical, primary store for all durable knowledge (learnings, research, decisions, project context, references)
- R2. auto-memory is migrated to Obsidian — MEMORY.md retains only a minimal pointer index. Note: Claude Code's built-in auto-memory will continue creating new content files; routing rules (R4) are conventions requiring ongoing compliance, not enforced constraints. Planning must address the regeneration management strategy
- R3. claude-mem retains its unique capabilities (cross-session timeline, smart_search) but operates as a read-heavy, write-light complement to Obsidian
- R4. Clear routing rules (conventions, not enforced constraints) define what knowledge goes where — no knowledge should require manual duplication across systems. Enforcement relies on CLAUDE.md instructions and session behavior, not technical locks

**Routing Rules**

- R5. Durable knowledge (compound learnings, research findings, technical decisions, project status, reference links) routes to Obsidian via obsidian-agent
- R6. Critical behavioral rules (architecture lessons, context hygiene guardrails) are surfaced in CLAUDE.md to guarantee auto-loading every session
- R6b. Session-to-session pointers (user identity, project state, references) remain in MEMORY.md as one-line entries pointing to Obsidian notes. Constraint: MEMORY.md pointers to vault paths outside the memory/ directory are NOT auto-loaded by Claude Code — the pointer pattern must be designed so Claude knows to read the referenced files (planning must validate this)
- R7. claude-mem receives structured observations from significant Obsidian writes (Obsidian → claude-mem bridge) via an in-session mechanism (slash command or automated prompt), not a post-session hook
- R8. auto-memory MEMORY.md entries should reference Obsidian notes for detail rather than duplicating content inline

**Integration**

- R9. A bridging mechanism syncs significant Obsidian content into claude-mem's index (direction: Obsidian → claude-mem). Must run within an active Claude session since claude-mem MCP tools require session context
- R10. _(merged into R8 and Success Criteria — quantitative limit "under 10 entries, each under 150 chars" lives in Success Criteria only)_

**Migration**

- R11. All 7 existing auto-memory content files migrate: `user_profile.md`, `project_dev-vault.md`, `feedback_architecture.md`, `feedback_context_hygiene.md`, `feedback_benchmark_first.md`, `reference_tools.md`, `reference_claude_agent_sdk_api.md` — durable knowledge → Obsidian notes, behavioral rules → CLAUDE.md, MEMORY.md → pointer-only index
- R12. Existing claude-mem observations that duplicate Obsidian content are identified (no automated deletion required — manual review is acceptable)

## Success Criteria

- Starting a new session, Claude can surface any prior durable knowledge without the user needing to specify which system holds it (either auto-loaded via CLAUDE.md/MEMORY.md, or Claude proactively searches obsidian/claude-mem when the topic arises)
- auto-memory MEMORY.md stays under 10 entries, each under 150 characters
- No durable knowledge exists only in auto-memory — it either lives in Obsidian or has a pointer to Obsidian
- claude-mem timeline reflects significant vault activity without requiring separate manual logging

## Scope Boundaries

- NOT redesigning obsidian-agent's core architecture or vault structure
- NOT building new MCP servers or tools from scratch
- NOT changing Claude Code's built-in auto-memory mechanism (it can't be disabled, only managed)
- NOT addressing plugin startup overhead (deferred to a follow-up brainstorm/plan)
- NOT changing the PARA structure or frontmatter schema of the vault

## Key Decisions

- **Obsidian as canonical store**: All durable knowledge lives in the vault. This was chosen over "consolidate to two" (dropping claude-mem) because claude-mem's timeline and cross-project search add unique value that Obsidian alone doesn't provide
- **claude-mem as complement, not competitor**: claude-mem stays for search and timeline but becomes write-light — primary writes go to Obsidian, claude-mem gets bridged summaries
- **auto-memory fully migrated**: All 6 existing auto-memory content files migrate to Obsidian. MEMORY.md retains only one-line pointers. Critical behavioral rules (architecture lessons, context hygiene) are promoted to CLAUDE.md to guarantee auto-loading
- **Behavioral rules in CLAUDE.md**: Feedback-type knowledge that must be loaded every session (e.g., "stop hooks can't use Claude", "/compact at 70%") lives in CLAUDE.md, not auto-memory or Obsidian alone. This ensures Claude follows guardrails from turn 1

## Dependencies / Assumptions

- obsidian-agent v0.7.0 is stable and provides the CLI commands needed for routing (journal, note, capture, search, suggest, cluster)
- claude-mem MCP tools (`smart_search`, `timeline`, `get_observations`) continue to work as-is
- The session-stop hook and bridge commands (bridge-plan, bridge-compound) already provide partial Obsidian → vault integration

## Outstanding Questions

### Resolved During Brainstorm

- **Bridge trigger** (R7, R9): ~~Session-stop hook batch sync~~ → Changed to in-session mechanism (slash command or automated prompt). Session-stop hooks run after Claude exits and cannot access MCP tools. The bridge must run within an active session where claude-mem MCP tools are available.
- **Migration scope** (R2, R6): All 6 auto-memory content files migrate to Obsidian. Critical behavioral feedback promotes to CLAUDE.md. MEMORY.md becomes pointer-only index.

### Deferred to Planning

- [Affects R9][Technical] Exact mechanism for in-session Obsidian → claude-mem bridging (slash command trigger, what data to extract, how to batch observations via claude-mem MCP tools)
- [Affects R11][Technical] Rollback strategy: backup auto-memory files before migration since ~/.claude/ has no git. Ensure original content is recoverable if pointer pattern or CLAUDE.md restructuring degrades session quality
- [Affects R6b][Needs research] Whether auto-memory MEMORY.md pointers to vault paths trigger Claude to read those files, or if the pointer pattern needs to be designed differently
- [Affects R11][Technical] Migration approach for each of the 6 existing auto-memory files — which Obsidian note type (project/resource/area) and which CLAUDE.md section for behavioral rules
- [Affects R6][Technical] How to restructure CLAUDE.md to absorb behavioral rules without making it too long (global CLAUDE.md is ~33 lines, project CLAUDE.md adds ~23 lines; feedback files total ~64 lines of behavioral content)

## Next Steps

→ `/ce:plan` for structured implementation planning

## Future Work (Out of Scope)

- Plugin startup overhead optimization via project-level profiles
- Plugin token overhead measurement and selective trimming
