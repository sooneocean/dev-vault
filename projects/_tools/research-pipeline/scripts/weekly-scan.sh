#!/bin/bash
# Research Pipeline — Weekly Deep Scan
# Scheduled via Windows Task Scheduler every Sunday at UTC 02:00
# Includes evaluation + Docker PoC for top candidates

set -euo pipefail

PIPELINE_DIR="/c/DEX_data/Claude Code DEV/projects/tools/research-pipeline"
VENV_DIR="$PIPELINE_DIR/.venv"
LOG_DIR="$PIPELINE_DIR/state"

TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
LOG_FILE="$LOG_DIR/weekly-scan-$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] Starting weekly deep-scan..." | tee "$LOG_FILE"

# Pre-flight: Ollama
if ! ollama list &>/dev/null 2>&1; then
    echo "WARNING: Ollama not running, starting..." | tee -a "$LOG_FILE"
    ollama serve &>/dev/null &
    sleep 5
fi

# Pre-flight: Docker
if ! docker info &>/dev/null 2>&1; then
    echo "WARNING: Docker not running. PoC tests will be skipped." | tee -a "$LOG_FILE"
fi

# Lock check
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

# Run deep scan
cd "$PIPELINE_DIR"
source "$VENV_DIR/Scripts/activate"

echo "Running deep-scan..." | tee -a "$LOG_FILE"
python orchestrator.py --mode deep-scan 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: Pipeline failed with exit code $EXIT_CODE" | tee -a "$LOG_FILE"
    # Send Telegram failure alert (if configured)
    python -c "
from schedule import send_failure_alert
send_failure_alert('deep-scan', 'Pipeline exited with code $EXIT_CODE', '$LOG_FILE')
" 2>/dev/null || true
fi

# Cleanup old Docker images
echo "Cleaning up PoC Docker images..." | tee -a "$LOG_FILE"
docker images --filter "reference=poc-*" --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | xargs -r docker rmi 2>/dev/null || true

echo "[$TIMESTAMP] Weekly scan complete (exit: $EXIT_CODE)" | tee -a "$LOG_FILE"
