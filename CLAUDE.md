# Obsidian Vault — Dev Knowledge Base

You manage a PARA-style Obsidian vault. Owner: sooneocean. Repo: `github.com/sooneocean/dev-vault`.

## Agent Rules (highest priority)

- IMPORTANT: ALWAYS use `obsidian-agent` CLI for vault operations — it handles frontmatter, linking, and index updates automatically. Fall back to manual edits ONLY when CLI is unavailable.
- MUST read `CONVENTIONS.md` before any manual edit — it defines frontmatter schema (subtype, maturity, domain, relation_map) and writing rules.
- See `AGENT.md` for CLI commands and directory structure.

## Compound Engineering Integration

- `docs/plans/` — Implementation plans (`/ce:plan`)
- `docs/solutions/` — Solved problem learnings (`/ce:compound`)
- `docs/brainstorms/` — Requirements documents (`/ce:brainstorm`)

## Behavioral Rules

### Architecture Constraints
- Stop hooks run AFTER Claude exits — Claude is NOT available. Any logic needing reasoning must run in an active session (slash command or user trigger).
- `~/.claude/` is NOT a git repo. Rollback strategy: project-level = git, global-level = `.bak` files.
- `.claude/commands/*.md` are prompt templates injected into active sessions, not executable scripts.

### Operational Rules
- 12 plugins consume ~10-15K tokens in tool definitions at session start. Be context-aware.
- Local LLM deployment: ALWAYS benchmark (pull + test) before writing plans. Model card estimates are unreliable (often 5-10x off for VRAM/speed).

### Knowledge Routing (Obsidian-first)
- Durable knowledge (learnings, research, decisions, references) → Obsidian vault via `obsidian-agent` CLI. Do NOT create auto-memory content files for durable knowledge.
- Session-to-session context → keep MEMORY.md as lean pointers (under 10 entries, each under 150 chars).
- session-wrap: when wrapping, prefer updating existing vault notes over creating new auto-memory files.

## Git

- Line endings: `.gitattributes` set to `* text=auto`
- `.claude/commands/` is tracked (slash command definitions)
- `projects/tools/` is gitignored (submodules)
