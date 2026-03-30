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

The `related` field uses plain `[[note]]` format for CLI compatibility. Semantic relation types are stored in the separate `relation_map` field.

**Format:** `relation_map: "note-a:documents, note-b:extends"`

| Type | Meaning | Example |
|------|---------|---------|
| `extends` | Builds upon or deepens another note | research note extends an area |
| `depends-on` | Requires another note's content | project depends on a resource |
| `implements` | Realizes or executes a plan/idea | project implements an idea |
| `documents` | Describes or records details of another note | architecture doc documents a project |
| `supersedes` | Replaces an older note | new research supersedes old version |
| `nav-prev` | Previous journal entry (journal only) | — |
| `nav-next` | Next journal entry (journal only) | — |

**When to use:** Only add `relation_map` when the relationship has clear semantics beyond "related". Not every `related` link needs a typed entry. CLI ignores this field (safe to add).

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

### `subtype: iteration-log` — Additional Fields

**Role:** Record a single iteration cycle for product development — proposals generated, features selected, and release completed.

**When to use:** After running `/iterate propose`, `/iterate confirm`, and `/iterate release` commands to document the full iteration workflow.

**Additional frontmatter fields:**

```yaml
subtype: iteration-log
version: string                 # Version released in this iteration (e.g., "1.2.3")
iteration_date: YYYY-MM-DD      # Date iteration was initiated
proposals_count: integer        # Number of proposals generated
selected_count: integer         # Number of features selected
github_release_url: string      # URL to GitHub release (set after release)
github_release_date: YYYY-MM-DD # Date of GitHub release (set after release)
```

**Sections:**

- **Proposals Generated** — Table of proposals with title, problem statement, effort estimate (S/M/L), value estimate (L/M/H), rank, and status
- **Features Selected** — Table of selected features with GitHub issue links and status
- **Release Record** — GitHub release link, generated changelog, version jump details
- **Iteration Notes** — Key dates: iteration started, selection finalized, release date

**File naming:** `YYYY-MM-DD-vX.Y.Z-iteration.md` (e.g., `2026-03-30-v1.2.3-iteration.md`)

**Use case:** Developers can browse iteration history, link to past proposals, understand what was shipped in which version, and track feature evolution.

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

1. **Read this file before writing**
2. **New notes must include complete frontmatter** (use actual values, not template placeholders)
3. **Update the `updated` field** when modifying notes
4. **Update the directory's `_index.md`**
5. **Update `_tags.md`** tag index
6. **Update `_graph.md`** relationship graph (if note has `[[]]` links or `related` field)
7. **Actively maintain `related` field** — search for related notes and build bidirectional links
8. **For area type**: update "Current Focus" and "Recent Progress" sections

## Using Templates

All templates are in `templates/` with `{{PLACEHOLDER}}` syntax. When creating notes:
1. Read the template for the note type
2. Replace all `{{}}` placeholders with actual values
3. Do not leave any unreplaced placeholders

## Using the CLI (recommended)

Instead of manual file operations, agents can use the `obsidian-agent` CLI.
The CLI handles frontmatter, linking, and index updates automatically.

```bash
# Create & read
obsidian-agent journal              # Create/open today's journal
obsidian-agent note "Title" type    # Create a note (auto-links related notes)
obsidian-agent capture "idea"       # Quick idea capture
obsidian-agent read "note"          # Read a note's content
obsidian-agent recent               # Recently updated notes (last 7 days)

# Search & discover
obsidian-agent search "keyword"     # Full-text search
obsidian-agent list [type]          # List notes with filters
obsidian-agent backlinks "note"     # What links here?
obsidian-agent orphans              # Find unlinked notes

# Edit existing notes (prefer over direct file editing)
obsidian-agent patch "note" --heading "Section" --append "content"
obsidian-agent update "note" --status active --summary "Updated"
obsidian-agent archive "old-note"   # Set status to archived
obsidian-agent delete "old-note"    # Delete and clean up references

# Tags
obsidian-agent tag list             # List all tags with counts
obsidian-agent tag rename "old" "new"

# Reviews
obsidian-agent review               # Weekly review
obsidian-agent review monthly       # Monthly review

# Discovery & analysis
obsidian-agent stale                # Find stale notes + triage plan
obsidian-agent cluster              # Topic clustering + missing links
obsidian-agent digest --all         # Project status dashboard
obsidian-agent thread "topic"       # Trace topic evolution over time
obsidian-agent suggest              # Smart daily action suggestions
obsidian-agent context "note"       # Full context around a note

# Maintenance
obsidian-agent sync                 # Rebuild tag & graph indices
obsidian-agent health               # Vault health score
obsidian-agent stats                # Vault statistics overview
obsidian-agent graph                # Generate Mermaid knowledge graph
```
