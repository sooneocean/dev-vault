Bridge a Compound Engineering plan document into the vault as a project note.

Usage: `<path-to-CE-plan-file>`
Example: `/bridge-plan docs/plans/2026-03-29-002-feat-obsidian-agent-efficiency-plan.md`

Steps:
1. Read the CE plan file at the given path (usually under `docs/plans/`)
2. Extract YAML frontmatter: `title`, `type`, `date`, `status`, `origin`
3. Run: `obsidian-agent note "<title>" project` to create a vault project note
4. Populate the note content:
   - Copy the `Overview` section from the plan
   - Copy the `Requirements Trace` (or list requirement IDs with brief descriptions)
   - Add implementation units as a checklist under a `## Progress` section
5. Update the note's frontmatter:
   - `tags`: `[plan, <type>]` (type is feat/fix/refactor from the plan)
   - `source`: relative path to the original plan file
   - `related`: start with `["[[tech-research-squad]]"]`
   - `summary`: one-line summary from the plan's Overview
   - `goal`: the plan's stated goal
6. If the `origin` field exists (points to a brainstorm file):
   - Search the vault for a note matching the brainstorm topic
   - If found, add bidirectional links between the new project note and the brainstorm-related note
7. Update bidirectional links on `tech-research-squad.md`
8. Run: `obsidian-agent sync` to rebuild indices

If the plan file does not exist, show an error.
If a vault note with the same title already exists, update it instead of creating a duplicate.

If the CLI is not available, follow CONVENTIONS.md manually:
- Read the project template from `templates/project.md`
- Replace all `{{}}` placeholders
- Write to `projects/`
- Update `_index.md`, `_tags.md`, `_graph.md`

$ARGUMENTS
