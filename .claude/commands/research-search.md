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

Search research notes using keyword and semantic matching.

Usage: /research-search <query>

Run:
```bash
cd "C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline"
source .venv/Scripts/activate
python -c "
from knowledge.vector_store import search
results = search('$ARGUMENTS')
for r in results:
    print(f'{r[\"score\"]:.2f} | {r[\"path\"]} | {r[\"section\"]}')
    print(f'  {r[\"text\"][:200]}')
    print()
"
```

If the knowledge layer (LanceDB) is not available, fall back to:
1. Use `obsidian-agent search "$ARGUMENTS"` for full-text search
2. Or use `grep -rl "$ARGUMENTS" resources/research-*.md` for basic matching
3. Display matching notes with context

$ARGUMENTS
