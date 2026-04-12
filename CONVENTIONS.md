---
title: Writing & Agent Conventions
type: meta
updated: 2026-03-29
---

# Conventions

## Required Frontmatter

```yaml
---
title: string          # Note title
type: string           # area | project | resource | journal | idea
tags: [string]         # Tag list
created: YYYY-MM-DD    # Created date
updated: YYYY-MM-DD    # Last updated date
status: string         # active | archived | draft (lifecycle state)
maturity: string       # seed | growing | mature (content quality — see Maturity below)
domain: string         # Controlled vocabulary (see Domains below)
summary: string        # One-line summary for agent retrieval
related: [[note]]      # Related notes list (optional for journal) — plain [[note]] format ONLY
relation_map: string   # Typed relations (optional) — format: "note-a:type, note-b:type" (see Relation Types)
---
```

## Optional Fields

```yaml
source: url            # Source link (common for resource type)
goal: string           # Project goal (project type)
deadline: YYYY-MM-DD   # Deadline (project type)
priority: high | medium | low
```

## Maturity

Describes content quality and completeness, independent of lifecycle `status`:

| Value | Meaning | When to use |
|-------|---------|-------------|
| `seed` | Initial idea, stub, or placeholder | Note has a title and maybe a few lines, but no substantial content |
| `growing` | Has real content but still developing | Active research, partial documentation, work in progress |
| `mature` | Complete and stable | Comprehensive content, unlikely to change significantly |

Note: `status` tracks lifecycle (active/archived/draft), `maturity` tracks content depth. A note can be `status: active, maturity: seed` (live but thin) or `status: archived, maturity: mature` (complete but no longer maintained).

## Domains

Controlled vocabulary for topic classification. Use exactly one value per note:

| Domain | Scope |
|--------|-------|
| `ai-engineering` | Claude Code, LLM tools, AI-assisted development, prompt engineering |
| `dev-environment` | Machine specs, OS config, dev tools, project layout |
| `open-source` | GitHub repos, publishing workflows, community standards |
| `knowledge-management` | Obsidian, vault structure, note-taking, PKM |
| `project-specific` | Specific project context (CSM, pretext, etc.) |

**Adding new domains:** Only add when 3+ notes would use the new domain and no existing domain fits. Update this table and the templates.

## Relation Types

`related: [[note]]` uses plain format for CLI compatibility. Use `relation_map` for semantic types: `"note-a:documents, note-b:extends"` (extends | depends-on | implements | documents | supersedes). Only add when relationship is clear; not every link needs typing.

## Subtypes

Resource notes **must** have a `subtype` field. Other types do not use subtypes. When in doubt between two subtypes, choose the one that best describes the note's **primary role**.

### Resource Subtypes

| Subtype | Role | When to use | Example notes |
|---------|------|-------------|---------------|
| `reference` | Static reference to a tool, library, or external concept | Describing what something IS, not evolving over time | compound-engineering-plugin, pretext engine |
| `research` | Accumulating research on a topic, updated over sprints | Growing knowledge base with sprint reflections | context-engineering-research, prompt-engineering-research |
| `catalog` | Inventory or listing of items | Enumerating machines, repos, tools, projects | dexg16-machine-specs, github-repo-list |
| `config` | Configuration documentation | Recording how something is configured | claude-code-configuration |
| `learning` | Lessons learned from solving a problem | Post-mortem style: what happened, what we learned | session-stop-wrapper-learning |
| `standard` | Process documentation or quality standards | Defining HOW to do something | github-發布流程, 開源專案品質標準 |
| `article` | Finished writing piece for external platforms | Finalized content for WordPress, Dev.to, etc. | 2026-03-31-writing-framework |
| `improvement` | Configuration improvement proposals from `/improve` | Auto-generated improvement suggestions | improvement-2026-03-29-001 |

### `subtype: improvement` — Additional Fields

```yaml
subtype: improvement
status: proposed | applied | rejected   # Lifecycle: proposed → applied/rejected
risk_level: low | medium | high         # low=new command, medium=vault config, high=global config
target_layer: project | global          # Which config layer is affected
target_file: string                     # Path to the config file to modify
friction_type: missing-hook | instruction-gap | command-gap
```

File naming: `improvement-YYYY-MM-DD-NNN.md` (e.g., `improvement-2026-03-29-001.md`)

### `subtype: article` — Additional Fields

```yaml
subtype: article
publish_status: draft | published | scheduled
target_site: yololab.net | other
wordpress_id: integer           # ID from WordPress after publishing
canonical_url: url              # Final live URL
excerpt: string                 # SEO description
```

### `subtype: iteration-log` — Product Iteration Records

Records iteration cycles (proposals → selection → release). Add `version`, `iteration_date`, `proposals_count`, `selected_count`, `github_release_url`, `github_release_date` fields. File naming: `YYYY-MM-DD-vX.Y.Z-iteration.md`

## File Naming

- Lowercase with hyphens: `my-note-title.md`
- Journal uses dates: `2026-03-27.md`
- Weekly review uses week numbers: `2026-W13-review.md`
- Each directory has `_index.md` as its index

## Tag Naming Rules

- **Format:** kebab-case, English only (e.g., `open-source`, not `開源`)
- **Specificity:** Prefer specific over abstract (`session-stop-hook` > `hook`)
- **No redundancy with schema:** Don't create tags that duplicate `subtype` or `domain` values (e.g., no `research` tag when `subtype: research` exists)
- **Minimum utility:** A tag should appear on 2+ notes. If creating a singleton tag, consider whether `domain` or `subtype` already covers the concept

## Content Rules

- Headings use `#`
- Keep text concise and direct
- Use `[[]]` for internal links
- Code blocks should specify language

## Agent Rules

1. Read CONVENTIONS.md before writing
2. Complete frontmatter required; no template placeholders left
3. Use `clausidian` CLI (handles rules 4-7 automatically)
4. If editing manually: update `updated` field, rebuild `_tags.md`/`_graph.md` via `clausidian sync`
5. Build bidirectional links via `related` field
6. For `area` type: update "Current Focus" and "Recent Progress" sections

## Using the CLI (recommended)

Prefer `clausidian` over manual edits — handles frontmatter, linking, and indices automatically. Full command reference in [AGENT.md](AGENT.md). Core commands:

```bash
clausidian journal              # Daily log
clausidian note "Title" type    # Create note (auto-links)
clausidian search "keyword"     # Full-text search
clausidian sync                 # Rebuild indices after manual edits
clausidian health               # Vault completeness score
```
