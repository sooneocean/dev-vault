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
- R2. auto-memory is minimized to session-critical context only: user preferences, active project pointers, and behavioral feedback that must be auto-loaded
- R3. claude-mem retains its unique capabilities (cross-session timeline, smart_search) but operates as a read-heavy, write-light complement to Obsidian
- R4. Clear, enforceable routing rules define what knowledge goes where — no knowledge should require manual duplication across systems

**Routing Rules**

- R5. Durable knowledge (compound learnings, research findings, technical decisions, project status, reference links) routes to Obsidian via obsidian-agent
- R6. Session-to-session context (user preferences, active state pointers, behavioral feedback rules) remains in auto-memory but as lean pointers, not full content
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
- **auto-memory as lean pointers**: auto-memory can't be disabled, but it can be kept minimal — pointers to Obsidian content rather than duplicating it

## Dependencies / Assumptions

- obsidian-agent v0.7.0 is stable and provides the CLI commands needed for routing (journal, note, capture, search, suggest, cluster)
- claude-mem MCP tools (`smart_search`, `timeline`, `get_observations`) continue to work as-is
- The session-stop hook and bridge commands (bridge-plan, bridge-compound) already provide partial Obsidian → vault integration

## Outstanding Questions

### Resolve Before Planning

- [Affects R7, R9][User decision] What triggers the Obsidian → claude-mem bridge? Options: (a) hook on obsidian-agent write commands, (b) manual bridge command, (c) session-stop hook batch sync
- [Affects R6, R10][User decision] Which current auto-memory entries should migrate vs. stay? Need to audit the 6 existing memory files

### Deferred to Planning

- [Affects R9][Technical] Exact mechanism for Obsidian → claude-mem bridging (hook script, slash command, or MCP tool chain)
- [Affects R10][Needs research] Whether auto-memory entries can reference vault paths that Claude will auto-follow, or if content must be inline
- [Affects R11][Technical] Migration script design for existing auto-memory → Obsidian content transfer

## Next Steps

→ Resolve the 2 blocking questions above, then `/ce:plan` for structured implementation planning

## Future Work (Out of Scope)

- Plugin startup overhead optimization via project-level profiles
- Plugin token overhead measurement and selective trimming
