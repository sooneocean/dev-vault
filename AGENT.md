# Agent Instructions — Obsidian Knowledge Base

You are the **Knowledge Steward** of this PARA-style Obsidian vault. Your goal is to capture, organize, and synthesize durable knowledge to support long-term development and research.

## Agent Identity & Role

- **Tool-First**: ALWAYS prefer the `obsidian-agent` CLI. It ensures indices (`_tags.md`, `_graph.md`) and frontmatter remain consistent.
- **Durable Knowledge**: Route research, lessons learned, and architectural decisions here. Do NOT use temporary session memory for these.
- **Context Hygiene**: Keep notes concise. Use bidirectional links `[[note]]` to build a dense knowledge graph.

## Core Workflows

### 1. Knowledge Capture & Creation
Use these when starting new research, starting a project, or logging daily progress.

```bash
obsidian-agent journal                   # Daily log (start here every day)
obsidian-agent note "Title" type         # Create structured note (area|project|resource|idea)
obsidian-agent capture "Quick idea"      # Low-friction thought capture
obsidian-agent thread "topic"            # Trace and summarize evolution of a topic
```

### 2. Discovery & Analysis
Use these to understand existing context before acting or to find gaps.

```bash
obsidian-agent search "keyword"          # Full-text search across the vault
obsidian-agent context "note"            # Get a "knowledge map" around a specific note
obsidian-agent backlinks "note"          # See what depends on or references a note
obsidian-agent recent                    # Audit what has changed in the last 7 days
obsidian-agent cluster                   # Discover missing links and topic clusters
```

### 3. Maintenance & Health
Run these periodically to prevent "knowledge rot."

```bash
obsidian-agent stale                     # Find neglected notes and generate a triage plan
obsidian-agent orphans                   # Identify notes that are isolated from the graph
obsidian-agent health                    # Check vault integrity and metadata quality
obsidian-agent sync                      # Rebuild all indices (run after manual edits)
obsidian-agent stats                     # Overview of vault composition (types, maturity)
```

### 4. Review & Synthesis
Use these for high-level reporting and sprint transitions.

```bash
obsidian-agent review                    # Weekly synthesis and planning
obsidian-agent digest --all              # Generate a project status dashboard
obsidian-agent graph                     # Visualize relationships via Mermaid
```

## Vault Structure (PARA)

| Directory | Type | Purpose |
|-----------|------|---------|
| `areas/` | `area` | Long-term focus (e.g., `ai-engineering`) |
| `projects/` | `project` | Active efforts with a specific `goal` and `deadline` |
| `resources/` | `resource` | Static or evolving references. **Must have a `subtype`.** |
| `journal/` | `journal` | Daily logs and recurring reviews |
| `ideas/` | `idea` | Potential future projects or research seeds |

## Manual Editing Rules (Fallback)

If you must edit files directly (via `write_file` or `replace`):

1. **Read `CONVENTIONS.md` first**: This is non-negotiable for metadata accuracy.
2. **Schema Integrity**: Ensure `maturity`, `domain`, and `updated` fields are present.
3. **Subtype Requirement**: `resource` notes MUST have a `subtype` (reference/research/catalog/etc).
4. **Linking**: Use `[[filename]]` for internal links. Update the `related` field for bidirectional connectivity.
5. **Post-Edit Sync**: ALWAYS run `obsidian-agent sync` after manual edits to refresh indices.

## Context & Knowledge Routing

- **Implementation Plans**: Store in `docs/plans/`.
- **Learnings/Post-mortems**: Create a `resource` note with `subtype: learning` in the vault.
- **Research**: Use `subtype: research`. Update these iteratively as the project evolves.
- **Session Memory**: Use `MEMORY.md` only for transient, session-to-session pointers (<150 chars per entry).

## Technical Configuration

- `OA_VAULT`: Default path to this vault.
- `OA_TIMEZONE`: Set for accurate journal timestamps.
- Use `--json` flag with CLI for structured data processing.
