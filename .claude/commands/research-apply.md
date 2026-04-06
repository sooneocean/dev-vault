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

Review and apply pending research pipeline integration proposals.

Run:
```bash
cd "C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline"

echo "=== Pending Integration Proposals ==="
if [ -d state/proposals ]; then
  for f in state/proposals/pending-*.json; do
    if [ -f "$f" ]; then
      python -c "
import json
proposals = json.load(open('$f'))
pending = [p for p in proposals if p.get('status') == 'pending']
for p in pending:
    risk = p['risk_level'].upper()
    print(f'  [{risk}] {p[\"title\"]}')
    print(f'    Tool: {p[\"tool_name\"]} — {p[\"tool_url\"]}')
    print(f'    Category: {p[\"category\"]}')
    if p.get('config_diff'):
        print(f'    Config diff: {p[\"config_diff\"][:200]}')
    if p.get('existing_tool'):
        print(f'    Replaces: {p[\"existing_tool\"]}')
    print(f'    Target: {p.get(\"target_file\", \"N/A\")}')
    print()
" 2>/dev/null
    fi
  done
else
  echo "No proposals directory found."
fi
```

After listing proposals, for each pending proposal:
1. Show the full description and rationale
2. For LOW risk (MCP additions): show the exact settings.json diff, ask for y/n
3. For MEDIUM risk (replacements): explain what changes and impact, ask for y/n
4. For HIGH risk (workflow): explain thoroughly, require explicit confirmation

On approval:
- Apply the config change (edit settings.json or target file)
- Run `cd "C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline" && python -c "from integrator import update_proposal_status; update_proposal_status('TOOL_NAME', 'applied')"`
- Create a git commit: `feat(pipeline): apply research proposal — TITLE`

On rejection:
- Run `cd "C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline" && python -c "from integrator import update_proposal_status; update_proposal_status('TOOL_NAME', 'rejected')"`

If no automated proposals exist:
1. Review recent research notes in `resources/research-scan-*.md`
2. For each high-potential discovery, assess integration with current toolchain
3. Present options: add as MCP server, add as Ollama model, add as pip dependency, or track for later
4. Only apply after explicit user confirmation (show diff before any config change)

$ARGUMENTS
