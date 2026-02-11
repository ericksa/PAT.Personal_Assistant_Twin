#!/bin/bash
# Stop all PAT sync workers

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping PAT Sync Workers...${NC}"
echo ""

# Kill by PID file if exists
for file in .calendar-worker.pid .email-worker.pid .reminders-worker.pid; do
    if [ -f "$file" ]; then
        PID=$(cat "$file")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${GREEN}Stopping worker (PID: $PID)...${NC}"
            kill "$PID"
        fi
        rm "$file"
    fi
done

# Kill all pat_sync_worker.py processes
PIDS=$(pgrep -f "python3.*pat_sync_worker.py" || true)

if [ -n "$PIDS" ]; then
    echo ""
    echo -e "${YELLOW}Stopping all sync workers...${NC}"
    for PID in $PIDS; do
        kill "$PID" 2>/dev/null && echo -e "${GREEN}  Stopped PID: $PID${NC}"
    done
fi

sleep 1

# Verify all stopped
REMAINING=$(pgrep -f "python3.*pat_sync_worker.py" || true)

if [ -z "$REMAINING" ]; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  All workers stopped successfully${NC}"
    echo -e "${GREEN}============================================${NC}"
else
    echo ""
    echo -e "${RED}Some workers still running:${NC}"
    echo "$REMAINING"
fi
echo ""