# System Quick Start — 2026-04-12

Essential information for working with this project.

## Files in System Prompt (~20K tokens)

| File | Purpose | Read this first if... |
|------|---------|----------------------|
| **CLAUDE.md** | Project overview + setup | You're new to the project |
| **CONVENTIONS.md** | Vault metadata rules | You're creating/editing notes |
| **AGENT.md** | Vault workflows | You need to manage knowledge |

Total system overhead: **~20K tokens/conversation** (optimized from ~42K)

## One-Minute Setup

```bash
# Python (watermark removal)
python -m venv .venv
.venv/Scripts/activate              # Windows
pip install -r requirements.txt
pytest tests/

# Node.js (automation)
npm install
npm test

# Vault
clausidian journal                  # Daily log
clausidian sync                     # Verify indices
```

## Most Important Commands

### Development
```bash
pytest tests/ -v                    # Python tests
npm test                            # Node.js tests
npm run optimize:featured           # SEO optimization
```

### Vault
```bash
clausidian journal                  # Start/continue daily log
clausidian note "Title" project     # Create note
clausidian search "keyword"         # Find information
clausidian sync                     # Rebuild indices after edits
```

### Configuration
```bash
# Set .env variables (if needed)
ANTHROPIC_API_KEY=sk-...
OA_VAULT=/path/to/vault
```

## Documentation Navigation

**"How do I set up?"**
→ CLAUDE.md § Quick Start

**"How do I write a vault note?"**
→ CONVENTIONS.md + AGENT.md

**"How do I configure watermark removal?"**
→ docs/CONFIG.md

**"Something doesn't work"**
→ docs/TROUBLESHOOT.md

**"What's the architecture?"**
→ docs/ARCHITECTURE.md

## Vault Note Template

```yaml
---
title: My Note Title
type: project                    # area | project | resource | journal | idea
status: active                   # active | archived | draft
maturity: growing               # seed | growing | mature
domain: ai-engineering          # your domain
summary: One-line description
created: 2026-04-12
updated: 2026-04-12
---

# My Note Title

Your content here...
```

For resource notes, also add: `subtype: reference | research | catalog | config | learning | standard | article`

## Common Issues (One-Liners)

| Problem | Solution |
|---------|----------|
| Python imports fail | `source .venv/bin/activate` or `.venv\Scripts\activate` (Windows) |
| Vault sync error | `clausidian sync` |
| Node warnings | Already fixed (added `"type": "module"` to package.json) |
| ComfyUI not found | Check `http://localhost:8188` in browser + verify .env settings |
| Path quoting errors | Already fixed in site-optimizer.js (use `node "path with spaces"`) |

## Environment Variables (.env)

```bash
# Required for watermark removal
# Leave blank if not using that feature

OA_VAULT=/path/to/obsidian/vault
OA_TIMEZONE=Asia/Taipei
ANTHROPIC_API_KEY=sk-...
WP_APP_USER=your_username
WP_APP_PASS=your_password
```

## Git Workflow

```bash
git checkout -b feature/my-feature
# ... make changes ...
pytest tests/ -v && npm test
git add .
git commit -m "feat: clear description of what changed"
git push origin feature/my-feature
```

Use conventional commits: `feat:`, `fix:`, `refactor:` (describe WHY)

## MCP Servers

**Active:** wpcom-mcp (WordPress site management)

**Disabled:** arxiv, huggingface, fetch (use WebSearch/WebFetch tools instead)

To enable a disabled server: rename `_disabled_NAME` → `NAME` in .mcp.json

## Performance Targets

- Python test suite: <30 seconds
- Node.js test suite: <10 seconds
- Full pytest run: <60 seconds
- Vault sync: <5 seconds

If slower: check for hanging processes or large files.

## Token Optimization (This Session)

✅ **CLAUDE.md** — 235 → 83 lines (65% smaller)
✅ **CONVENTIONS.md** — 235 → 151 lines (36% smaller)
✅ **docs/README.md** — Split into CONFIG.md + TROUBLESHOOT.md
✅ **site-optimizer.js** — Fixed Windows path quoting bug

**Result:** ~15K tokens saved per conversation

## Next Steps

1. Run: `pytest tests/ -v` + `npm test` (verify everything works)
2. Run: `clausidian journal` (start daily log)
3. Check CLAUDE.md for any questions
4. Create a note: `clausidian note "My First Note" idea`

---

**Last Updated:** 2026-04-12 | **System Overhead:** ~20K tokens/conversation
