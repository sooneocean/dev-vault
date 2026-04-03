# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Python Environment (Watermark Removal System)
```bash
python -m venv .venv
.venv/Scripts/activate  # Windows
# OR source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
pytest tests/              # Run all tests
pytest tests/ -v           # Verbose output
pytest tests/test_foo.py   # Single test file
```

### Node.js Environment (Knowledge Management)
```bash
npm install
npm test                   # Run Jest tests
npm run test:watch        # Watch mode
npm run test:proposal     # Proposal engine tests only
npm run test:proposal-integration  # Integration tests (use --forceExit)
```

## Project Architecture

**Hybrid Python + Node.js Project**

- **Python Core**: `src/watermark_removal/` — Computer vision system for watermark removal using OpenCV, NumPy, scikit-image
  - `core/` — Pipeline orchestration, config management, types
  - `annotation/` — Label Studio integration, dataset export
  - `blending/` — Poisson blending and post-processing algorithms
  - `tests/` — Pytest suite (3.12, 3.13, 3.14 CI compatibility)

- **Node.js Layer**: Knowledge management, GitHub API integration, Anthropic SDK
  - `.claude/lib/` — Custom slash commands (proposal engine, etc.)
  - Jest test suite in `test/`
  - Dependencies: `@anthropic-ai/sdk`, `@octokit/rest`, `clausidian` (MCP integration)

- **Obsidian Vault**: PARA-structured knowledge base (managed via Clausidian CLI)
  - `areas/` — Long-term focus domains (ai-engineering, dev-environment, etc.)
  - `projects/` — Active initiatives (YOLO LAB, watermark removal system, etc.)
  - `resources/` — References, research, learnings, configs
  - `journal/` — Daily logs and weekly reviews
  - `ideas/` — Potential future work
  - Governed by `CONVENTIONS.md` (frontmatter schema, maturity levels, domains)

- **Automation & Scripts**: `scripts/` directory
  - `benchmark_phase3.py` — Performance tuning via Optuna
  - `label_studio_setup.py` — Data annotation pipeline
  - `batch_publisher.py`, `batch_tag_allocator.py` — WordPress SEO batch ops
  - `yolo_lab_seo_optimizer.js` — Website SEO optimization
  - `session_stop_wrapper.sh` — Vault sync hook (runs on Claude exit)

## Key Workflows

### Development Cycle

1. **Branch & Test Locally**
   ```bash
   git checkout -b feature/my-feature
   pytest tests/ -v    # Python changes
   npm test            # Node.js changes
   ```

2. **CI/CD**: GitHub Actions runs Python (3.12-3.14) and Node.js (v24) tests on push/PR

3. **Vault Integration**: Changes are synced via `clausidian` CLI (see AGENT.md for commands)

### Python Development
- **Config**: YAML files in `config/` directory
- **Testing**: `pytest` with `pytest-asyncio` for async operations
- **Benchmarking**: `scripts/benchmark_phase3.py` uses Optuna for hyperparameter tuning
- **Type Hints**: Check `src/watermark_removal/core/types.py` for domain objects

### Node.js Development
- **Proposal Engine**: `.claude/lib/proposal-engine.js` — Custom logic for decisions
- **GitHub API**: Uses Octokit for PR/issue automation
- **Anthropic SDK**: For Claude API integration
- **Fallback to Manual**: If `clausidian` CLI unavailable, follow rules in AGENT.md § Manual Editing Rules

## Knowledge Management (Vault)

**Setup** (Clausidian integration):
```bash
npm install -g clausidian
clausidian setup ~/my-vault    # Enable MCP integration + install /obsidian skill
```

**Core Rules** (from AGENT.md & CONVENTIONS.md):
- **Tool-First**: Always prefer `clausidian` CLI for consistency
- **Durable Knowledge**: Route research, learnings, architectural decisions to vault (not temp session memory)
- **Frontmatter Required**: Every note must have `title`, `type`, `created`, `updated`, `status`, `maturity`, `domain`, `summary`
- **Resource Notes**: Must include `subtype` (reference/research/catalog/config/learning/standard/article)
- **Context Routing**:
  - Implementation plans → `docs/plans/` (via `/ce:plan`)
  - Requirements → `docs/brainstorms/` (via `/ce:brainstorm`)
  - Solved problems → `resource` notes with `subtype: learning`

**Common Commands**:
```bash
clausidian journal              # Create/open today's journal entry
clausidian note "Title" project # Create new note (area|project|resource|idea)
clausidian capture "Idea"       # Quick idea capture
clausidian search "keyword"     # Full-text search across vault
clausidian health               # Score vault (0-100) on completeness & organization
clausidian sync                 # Rebuild tag and knowledge graph indices
clausidian graph                # Generate Mermaid knowledge diagram
clausidian daily                # Dashboard view
clausidian review               # Generate weekly review
clausidian review monthly       # Generate monthly review
clausidian read <note>          # View note content
clausidian backlinks <note>     # Show what references a note
clausidian stats                # Vault statistics and top tags
```

**Advanced Operations**:
```bash
clausidian rename <note> <title>    # Rename with reference updates
clausidian merge <source> <target>  # Combine notes
clausidian archive <note>           # Set status to archived
clausidian tag rename <old> <new>   # Rename tags vault-wide
clausidian link                     # Auto-link related notes
clausidian duplicates               # Find similar notes
clausidian focus                    # Suggest what to work on next
clausidian export [file]            # Export to JSON/markdown
clausidian import <file>            # Import from JSON/markdown
```

**Useful Flags**:
- `--vault <path>` — Specify vault location
- `--type <type>` — Filter by note type
- `--json` — Machine-readable output
- `--dry-run` — Preview changes before applying

## External Dependencies

- **FFmpeg**: Required for video processing workflows (check `docker-compose.*.yml`)
- **Docker**: Used for Label Studio, ComfyUI workflows
- **ComfyUI**: External workflow engine (see `workflows/` JSON files)
- **Label Studio**: Data annotation platform (initialized via `scripts/label_studio_setup.py`)

## Environment Variables

Set in `.env` or shell:
- `OA_VAULT`: Path to Obsidian vault (defaults to repo root)
- `OA_TIMEZONE`: Timezone for journal timestamps

## Testing

| Command | Purpose | CI Support |
|---------|---------|-----------|
| `pytest tests/` | Full test suite | ✅ (py3.12-3.14) |
| `pytest tests/ -v` | Verbose output | ✅ |
| `npm test` | Jest unit tests | ✅ (Node 24) |
| `npm run test:proposal` | Proposal engine only | ✅ |
| `npm run test:proposal-integration` | Integration tests (use --forceExit) | ✅ |

## Git & Configuration

- **Line Endings**: `.gitattributes` set to `* text=auto`
- **Tracked**: `.claude/commands/` (prompt templates for slash commands)
- **Ignored**: `projects/tools/` (submodules), `.venv`, `node_modules`, `__pycache__`
- **Commit Style**: Conventional commits (feat:, fix:, refactor:) — describe WHY, not WHAT
- **Branches**: main/master (CI runs on push and PR)

## Operational Constraints

1. **Stop Hooks**: `session_stop_wrapper.sh` runs AFTER Claude exits — no reasoning available
2. **Context Hygiene**: Use `/compact` at natural breakpoints; use `/clear` after 2+ failures or compacts
3. **Token Limits**: Plugin tools ~10-15K; use subagents for >50K output or 3+ large files
4. **Rollback**: Project-level changes = git; global config = `.bak` files

## Troubleshooting

- **Proposal engine fails**: Check `.claude/lib/proposal-engine.js` and test via `npm run test:proposal`
- **Python import errors**: Ensure `.venv` is activated and `pip install -r requirements.txt` completed
- **Vault inconsistencies**: Run `clausidian sync` to rebuild indices
- **Label Studio setup fails**: Check FFmpeg availability and Docker daemon status

## References

- [Architecture (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md) — Deep dive on watermark removal system
- [CONVENTIONS.md](CONVENTIONS.md) — Vault metadata schema and writing rules
- [AGENT.md](AGENT.md) — Clausidian CLI commands and knowledge routing
- [Phase Reports (docs/reports/)](docs/reports/) — Completed milestones
