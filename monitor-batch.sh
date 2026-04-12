#!/bin/bash
# Monitor batch processing progress

LOG_FILE="/c/DEX_data/Claude Code DEV/seo-batch-v3-final.log"
CHECKPOINT="/c/DEX_data/Claude Code DEV/seo-optimization-output/checkpoint.json"

echo "=== SEO Batch Processor Monitor ==="
echo "Started: $(grep '\[START\]' "$LOG_FILE" | tail -1)"
echo ""

if [ -f "$CHECKPOINT" ]; then
    echo "Latest Checkpoint:"
    cat "$CHECKPOINT" | grep -E "processed|updated|failed|timestamp"
    echo ""
fi

echo "Recent Progress:"
tail -20 "$LOG_FILE" | grep -E "PAGE|CHECKPOINT|^\[" | tail -10

echo ""
echo "Process Status:"
ps aux | grep "wp-seo-batch-v3" | grep -v grep && echo "RUNNING" || echo "COMPLETED/NOT RUNNING"
