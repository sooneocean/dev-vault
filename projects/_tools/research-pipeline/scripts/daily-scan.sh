#!/bin/bash
# Research Pipeline — Daily Quick Scan
# Scheduled via Windows Task Scheduler at UTC 06:00
# Uses claude -p with restricted permissions

set -euo pipefail

PIPELINE_DIR="/c/DEX_data/Claude Code DEV/projects/tools/research-pipeline"
VENV_DIR="$PIPELINE_DIR/.venv"
LOG_DIR="$PIPELINE_DIR/state"

# Timestamp
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
LOG_FILE="$LOG_DIR/daily-scan-$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] Starting daily quick-scan..." | tee "$LOG_FILE"

# Pre-flight checks
if ! command -v ollama &>/dev/null; then
    echo "WARNING: Ollama not found, skipping embedding step" | tee -a "$LOG_FILE"
fi

if ! ollama list &>/dev/null 2>&1; then
    echo "WARNING: Ollama not running, starting..." | tee -a "$LOG_FILE"
    ollama serve &>/dev/null &
    sleep 5
fi

# Check lock
if [ -f "$PIPELINE_DIR/state/pipeline.lock" ]; then
    LOCK_AGE=$(python -c "
import json, datetime
d = json.load(open('$PIPELINE_DIR/state/pipeline.lock'))
age = (datetime.datetime.now() - datetime.datetime.fromisoformat(d['locked_at'])).total_seconds() / 3600
print(f'{age:.1f}')
" 2>/dev/null || echo "999")

    if (( $(echo "$LOCK_AGE < 6" | bc -l) )); then
        echo "ERROR: Pipeline lock active (${LOCK_AGE}h old). Skipping." | tee -a "$LOG_FILE"
        exit 0
    fi
fi

# Run the scan
cd "$PIPELINE_DIR"
source "$VENV_DIR/Scripts/activate"

echo "Running quick-scan..." | tee -a "$LOG_FILE"
python orchestrator.py --mode quick-scan 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: Pipeline failed with exit code $EXIT_CODE" | tee -a "$LOG_FILE"
    # Send Telegram failure alert (if configured)
    python -c "
from schedule import send_failure_alert
send_failure_alert('quick-scan', 'Pipeline exited with code $EXIT_CODE', '$LOG_FILE')
" 2>/dev/null || true
fi

echo "[$TIMESTAMP] Daily scan complete (exit: $EXIT_CODE)" | tee -a "$LOG_FILE"
