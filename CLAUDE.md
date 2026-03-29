# Obsidian Vault — Dev Knowledge Base

PARA-style Obsidian vault managed by `obsidian-agent` CLI and Claude Code slash commands.
Owner: sooneocean. Public repo: `github.com/sooneocean/dev-vault`.

## Agent Rules

- IMPORTANT: For vault operations, ALWAYS use `obsidian-agent` CLI first — it handles frontmatter, linking, and index updates automatically.
- Before manual edits, MUST read `CONVENTIONS.md` for writing rules, frontmatter schema (incl. subtype, maturity, domain, relation_map).
- For CLI commands and directory structure, see `AGENT.md`.

## Compound Engineering Integration

- `docs/plans/` — Implementation plans (`/ce:plan`)
- `docs/solutions/` — Solved problem learnings (`/ce:compound`)
- `docs/brainstorms/` — Requirements documents (`/ce:brainstorm`)

## Git

- Line endings: `.gitattributes` set to `* text=auto`
- `.claude/commands/` is tracked (slash command definitions)
- `projects/tools/` is gitignored (submodules)
