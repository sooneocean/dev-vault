Review and apply pending research pipeline integration proposals.

Run:
```bash
cd "C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline"

echo "=== Pending Proposals ==="
# Find evaluation results with poc_candidate verdict
for f in state/eval-results-*.json; do
  if [ -f "$f" ]; then
    python -c "
import json
results = json.load(open('$f'))
candidates = [r for r in results if r.get('verdict') == 'poc_candidate']
for c in candidates:
    sr = c['scan_result']
    print(f\"  [{c['total_score']}/{c['max_score']}] {sr['name']} — {sr['url']}\")
    print(f\"    Tags: {', '.join(sr.get('tags', []))}\")
    print(f\"    Action: {c.get('recommended_action', 'N/A')}\")
    print()
" 2>/dev/null
  fi
done
```

If no automated proposals exist:
1. Review recent research notes in `resources/research-scan-*.md`
2. For each high-potential discovery, assess integration with current toolchain
3. Present options: add as MCP server, add as Ollama model, add as pip dependency, or track for later
4. Only apply after explicit user confirmation (show diff before any config change)

$ARGUMENTS
