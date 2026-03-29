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
- R2. auto-memory is fully migrated to Obsidian — MEMORY.md retains only a minimal pointer index (no content files)
- R3. claude-mem retains its unique capabilities (cross-session timeline, smart_search) but operates as a read-heavy, write-light complement to Obsidian
- R4. Clear, enforceable routing rules define what knowledge goes where — no knowledge should require manual duplication across systems

**Routing Rules**

- R5. Durable knowledge (compound learnings, research findings, technical decisions, project status, reference links) routes to Obsidian via obsidian-agent
- R6. Critical behavioral rules (architecture lessons, context hygiene guardrails) are surfaced in CLAUDE.md to guarantee auto-loading every session
- R6b. Session-to-session pointers (user identity, project state, references) remain in MEMORY.md as one-line entries pointing to Obsidian notes
- R7. claude-mem receives structured observations from significant Obsidian writes (bridge mechanism) to maintain its searchable index and timeline
- R8. auto-memory MEMORY.md entries should reference Obsidian notes for detail rather than duplicating content inline

**Integration**

- R9. A bridging mechanism syncs significant Obsidian content into claude-mem's index (direction: Obsidian → claude-mem)
- R10. auto-memory files for this project stay under 10 entries in MEMORY.md and lean toward pointers over prose

**Migration**

- R11. Existing auto-memory content that qualifies as durable knowledge migrates to appropriate Obsidian locations
- R12. Existing claude-mem observations that duplicate Obsidian content are identified (no automated deletion required — manual review is acceptable)

## Success Criteria

- Starting a new session, any prior knowledge is findable within one query (either auto-loaded from memory or discoverable via obsidian search / claude-mem smart_search)
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

- **Bridge trigger** (R7, R9): Session-stop hook batch sync — extends the existing session-stop wrapper pattern. Chosen over per-write hooks (too noisy) and manual commands (defeats the purpose).
- **Migration scope** (R2, R6): All 6 auto-memory content files migrate to Obsidian. Critical behavioral feedback promotes to CLAUDE.md. MEMORY.md becomes pointer-only index.

### Deferred to Planning

- [Affects R9][Technical] Exact mechanism for Obsidian → claude-mem bridging in the session-stop hook (what data to extract, how to call claude-mem MCP tools from a shell script)
- [Affects R6b][Needs research] Whether auto-memory MEMORY.md pointers to vault paths trigger Claude to read those files, or if the pointer pattern needs to be designed differently
- [Affects R11][Technical] Migration approach for each of the 6 existing auto-memory files — which Obsidian note type (project/resource/area) and which CLAUDE.md section for behavioral rules
- [Affects R6][Technical] How to restructure CLAUDE.md to absorb behavioral rules without making it too long (current CLAUDE.md is ~20 lines)

## Next Steps

→ `/ce:plan` for structured implementation planning

## Future Work (Out of Scope)

- Plugin startup overhead optimization via project-level profiles
- Plugin token overhead measurement and selective trimming
