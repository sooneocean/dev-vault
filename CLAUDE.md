# Obsidian Vault — Dev Knowledge Base

## What This Is

PARA-style Obsidian vault managed by `obsidian-agent` CLI and Claude Code slash commands.
Owner: sooneocean. Public repo: `github.com/sooneocean/dev-vault`.

## Directory Structure

| Directory    | Type     | Purpose                    |
|-------------|----------|----------------------------|
| `areas/`    | area     | Long-term focus areas       |
| `projects/` | project  | Concrete projects with goals|
| `resources/`| resource | Reference materials         |
| `journal/`  | journal  | Daily logs & weekly reviews |
| `ideas/`    | idea     | Draft ideas to explore      |

Special files: `_index.md` (per-directory index), `_tags.md`, `_graph.md`.

## Agent Rules (Critical)

1. **Use `obsidian-agent` CLI first** — it handles frontmatter, linking, and index updates automatically
2. If CLI unavailable, follow `CONVENTIONS.md` strictly
3. Every note needs complete frontmatter (title, type, tags, created, updated, status, summary, related)
4. **Always update** after changes: `updated` field, directory `_index.md`, `_tags.md`, `_graph.md`
5. Maintain **bidirectional links** via `related` field
6. File names: lowercase-hyphen (`my-note.md`), journals: `YYYY-MM-DD.md`, weekly: `YYYY-WXX-review.md`
7. Internal links: `[[filename]]` without `.md`
8. Templates in `templates/` use `{{PLACEHOLDER}}` — replace ALL before saving

## Slash Commands

| Command    | What it does                        |
|-----------|--------------------------------------|
| `/journal` | Create/open today's journal          |
| `/note`    | Create a note (title + type)         |
| `/capture` | Quick idea capture                   |
| `/search`  | Full-text search across vault        |
| `/list`    | List notes with filters              |
| `/review`  | Generate weekly review               |
| `/improve` | Analyze usage & suggest config improvements |

## CLI Quick Reference

```bash
# Set vault path to avoid --vault flag
export OA_VAULT="/c/DEX_data/Claude Code DEV"

# Common operations
obsidian-agent journal                   # today's journal
obsidian-agent note "Title" project      # new note
obsidian-agent capture "Quick idea"      # idea capture
obsidian-agent search "keyword"          # search
obsidian-agent list --recent 7           # recent notes
obsidian-agent review                    # weekly review
obsidian-agent sync                      # rebuild indices
obsidian-agent health                    # vault health check
```

## Templates Available

area, project, resource, idea, journal, weekly-review, monthly-review, note (generic), improvement

## Git

- Line endings: `.gitattributes` set to `* text=auto`
- `.claude/commands/` is tracked (slash command definitions)
- `projects/tools/` is gitignored (submodules)
