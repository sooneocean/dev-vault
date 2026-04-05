---
title: Untitled
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

Bridge a Compound Engineering learning document into the vault as a resource note.

Usage: `<path-to-CE-compound-file>`
Example: `/bridge-compound docs/solutions/workflow-issues/my-fix-2026-03-29.md`

Steps:
1. Read the CE compound file at the given path (usually under `docs/solutions/[category]/`)
2. Extract YAML frontmatter: `title`, `date`, `category`, `problem_type`, `severity`
3. Run: `obsidian-agent note "<title>" resource` to create a vault resource note
4. Run: `obsidian-agent patch "<title>" --heading "Summary" --replace "<Problem + Solution summary from the CE file>"`
5. Update the note's frontmatter:
   - `subtype`: `learning`
   - `maturity`: `seed`
   - `domain`: infer from CE `category` field — map to closest controlled vocabulary value (ai-engineering, dev-environment, open-source, knowledge-management, project-specific). Default to `project-specific` if unclear.
   - `tags`: `[compound-learning, <category>, <severity>]`
   - `source`: relative path to the original CE file (e.g., `docs/solutions/workflow-issues/my-fix.md`)
   - `related`: `["[[tech-research-squad]]"]` plus any related project if inferable from CE metadata
   - `relation_map`: `"tech-research-squad:extends"` plus any additional typed relations
   - `summary`: one-line summary of the problem and solution
6. Update bidirectional links: add `[[<new-note>]]` to `tech-research-squad.md`'s related field
7. Run: `obsidian-agent sync` to rebuild indices

If the CE file does not exist, show an error and list available files under `docs/solutions/`.
If a vault note with the same title already exists, update it instead of creating a duplicate.

If the CLI is not available, follow CONVENTIONS.md manually:
- Read the resource template from `templates/resource.md`
- Replace all `{{}}` placeholders
- Write to `resources/`
- Update `_index.md`, `_tags.md`, `_graph.md`

$ARGUMENTS
