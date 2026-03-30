Show research pipeline status: recent scans, pending proposals, model stats.

Run:
```bash
cd "C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline"

echo "=== Recent Scans ==="
ls -la state/scan-results-*.json 2>/dev/null | tail -5 || echo "No scan results yet"

echo ""
echo "=== Evaluation Results ==="
ls -la state/eval-results-*.json 2>/dev/null | tail -5 || echo "No evaluations yet"

echo ""
echo "=== Seen URLs ==="
if [ -f state/seen_urls.json ]; then
  python -c "import json; d=json.load(open('state/seen_urls.json')); print(f'{len(d)} URLs tracked')"
else
  echo "No URLs tracked yet"
fi

echo ""
echo "=== Pipeline Lock ==="
if [ -f state/pipeline.lock ]; then
  cat state/pipeline.lock
else
  echo "No active lock"
fi

echo ""
echo "=== Integration Proposals ==="
if [ -d state/proposals ]; then
  python -c "
import json, glob
pending = applied = rejected = 0
for f in glob.glob('state/proposals/pending-*.json'):
    for p in json.load(open(f)):
        s = p.get('status', 'pending')
        if s == 'pending': pending += 1
        elif s == 'applied': applied += 1
        elif s == 'rejected': rejected += 1
print(f'Pending: {pending}  Applied: {applied}  Rejected: {rejected}')
" 2>/dev/null
else
  echo "No proposals yet"
fi

echo ""
echo "=== Research Notes ==="
ls -la "C:\DEX_data\Claude Code DEV\resources\research-scan-"*.md 2>/dev/null | tail -5 || echo "No research notes yet"
```

If the pipeline directory is not available:
1. List recent `resources/research-scan-*.md` and `resources/research-deep-*.md` notes
2. Summarize: total scans, discoveries found, tools evaluated

$ARGUMENTS
