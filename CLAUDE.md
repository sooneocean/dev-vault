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

## Git

- Line endings: `.gitattributes` set to `* text=auto`
- `.claude/commands/` is tracked (slash command definitions)
- `projects/tools/` is gitignored (submodules)
