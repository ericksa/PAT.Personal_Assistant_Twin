#!/bin/bash
# scripts/start_sync_workers.sh - Start PAT sync workers in background

LOG_FILE="logs/sync_worker.log"
PID_FILE="logs/sync_worker.pid"

mkdir -p logs

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Sync worker is already running (PID: $PID)"
        exit 1
    else
        echo "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

echo "Starting PAT sync worker..."
nohup python3 scripts/pat_sync_worker.py >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "Sync worker started with PID $(cat "$PID_FILE")"
echo "Logs are being written to $LOG_FILE"
