# Obsidian Vault — Dev Knowledge Base

You manage a PARA-style Obsidian vault. Owner: sooneocean. Repo: `github.com/sooneocean/dev-vault`.

## Agent Operational Guidelines

### Core Responsibilities
- **Knowledge Steward**: Your primary role is to manage and synthesize durable knowledge within this Obsidian vault.
- **Tool First**: ALWAYS use the `obsidian-agent` CLI for vault operations. It ensures frontmatter, linking, and index updates are handled consistently. Fall back to manual edits ONLY when the CLI is unavailable.
- **Convention Adherence**: MUST read and follow `CONVENTIONS.md` before any manual edit. This file defines the frontmatter schema and writing rules.
- **Command Reference**: Refer to `AGENT.md` for a comprehensive list of CLI commands and vault directory structure.

### Knowledge Management & Routing
- **Durable Knowledge**: Route all learnings, research, decisions, and references to your Obsidian vault via `obsidian-agent` CLI. Do NOT create auto-memory content files for durable knowledge.
- **Session Context**: Use `MEMORY.md` only for transient, session-to-session pointers (under 10 entries, each under 150 chars).
- **PARA Structure**: Organize information according to the vault's PARA structure (Projects, Areas, Resources, Archives).

### Workflow & Operational Guidelines
- **Compound Engineering Integration**:
    - Implementation plans: Store in `docs/plans/` (use `/ce:plan`).
    - Solved problem learnings: Store as `resource` notes with `subtype: learning` in the vault.
    - Requirements documents: Store in `docs/brainstorms/` (use `/ce:brainstorm`).
- **Operational Awareness**: Be context-aware of token limits (~10-15K for plugin tools). For local LLM deployment, ALWAYS benchmark (pull + test) before writing plans; estimates are often unreliable.
- **Execution Constraints**:
    - Stop hooks run AFTER Claude exits; Claude is NOT available. Any logic needing reasoning must run in an active session (slash command or user trigger).
    - `~/.claude/` is NOT a git repo. Rollback strategy: project-level = git, global-level = `.bak` files.
    - `.claude/commands/*.md` are prompt templates for active sessions, not executable scripts.

### Environment & Git
- **Git Configuration**:
    - Line endings: `.gitattributes` is set to `* text=auto`.
    - Tracked files: `.claude/commands/` is tracked.
    - Ignored files: `projects/tools/` is gitignored (submodules).
- **Vault Path**: The `OA_VAULT` environment variable specifies the default vault path.
- **Timezone**: The `OA_TIMEZONE` environment variable should be set for accurate journal timestamps.
