# CLAUDE.md

Quick reference for working with this hybrid Python + Node.js project. See referenced docs for details.

## Quick Start

### Python (Watermark Removal)
```bash
python -m venv .venv
.venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest tests/ -v
```

### Node.js (Knowledge Management)
```bash
npm install
npm test                           # Jest suite
npm run test:proposal             # Proposal engine only
npm run test:proposal-integration --forceExit
```

## Project Structure

- **Python**: `src/watermark_removal/` — CV pipeline (detection, inpainting, blending, temporal state)
- **Node.js**: `.claude/lib/` — CLI commands, GitHub API, Anthropic SDK
- **Vault**: Obsidian PARA structure (areas/, projects/, resources/, journal/, ideas/)
- **Scripts**: `scripts/` — benchmarking, Label Studio, WordPress batch ops, SEO optimization

## Key Workflows

**Development**: `git checkout -b feature/X` → test locally → CI/CD on push/PR → sync via `clausidian`

**Python Testing**: `pytest tests/ -v` (3.12-3.14 compatibility)

**Node.js**: Proposal engine (`.claude/lib/proposal-engine.js`), GitHub API wrapper (`.claude/lib/github-api.js`), changelog generation

**Vault**: Use `clausidian` CLI (see AGENT.md for full command list). Core rules in CONVENTIONS.md.

## MCP Servers

| Server | Status | Purpose |
|--------|--------|---------|
| **wpcom-mcp** | ✅ | WordPress.com site management |
| **chrome-devtools-mcp** | ✅ | Browser debugging and testing |
| **context7** | ✅ | Framework documentation caching |
| **github** | ✅ | GitHub API integration |
| **claude-mem** (agent-memory) | ❌ | Disabled — conflicts with obsidian-agent vault management |
| **arxiv, huggingface, fetch** | ❌ | Disabled (use WebSearch/WebFetch instead) |

Test: `npm run test:proposal-integration --forceExit`

## Configuration & Environment

- **Config**: YAML in `config/`
- **.env vars**: `OA_VAULT`, `OA_TIMEZONE`, `WP_APP_USER`, `WP_APP_PASS`, `WP_BEARER_TOKEN`, `ANTHROPIC_API_KEY`
- **Git**: Conventional commits (feat:, fix:, refactor:) — describe WHY
- **.gitignore**: `_tools/`, `.venv`, `node_modules`, `__pycache__`

## Operational Constraints

1. Context hygiene: `/compact` at natural breaks; `/clear` after 2+ failures
2. Token limits: Use subagents for >50K output or 3+ large files
3. Stop hooks: `session_stop_wrapper.sh` runs AFTER Claude exits
4. Rollback: Git (code) or `.bak` files (config)

## Testing & CI/CD

```
pytest tests/              # Full Python suite
npm test                   # Jest suite
GitHub Actions: Python 3.12-3.14 + Node v24
```

## Troubleshooting

- **Python imports**: Activate `.venv` and run `pip install -r requirements.txt`
- **Vault issues**: `clausidian sync` to rebuild indices
- **Proposal engine**: Check `.claude/lib/proposal-engine.js` and run `npm run test:proposal`
- **SEO scripts**: Set `ANTHROPIC_API_KEY`, test with `--demo` flag

## References

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Watermark removal system deep dive
- [AGENT.md](AGENT.md) — Clausidian CLI commands, vault routing rules
- [CONVENTIONS.md](CONVENTIONS.md) — Vault metadata schema
- [Phase Reports](docs/reports/) — Milestone documentation
