#!/bin/bash
# Start all PAT sync workers in background
# This script launches all three workers for continuous sync

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Starting PAT Sync Workers${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Check if PAT Core is running
if curl -s http://localhost:8010/pat/health > /dev/null; then
    echo -e "${GREEN}✓ PAT Core is running${NC}"
else
    echo -e "${YELLOW}⚠ Warning: PAT Core may not be running${NC}"
    echo -e "  Start it: cd src && python3 main_pat.py"
    echo ""
fi

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}✗ Error: Sync workers only work on macOS${NC}"
    echo "  Current OS: $OSTYPE"
    exit 1
fi

# Ensure logs directory exists
mkdir -p logs

# Function to start a worker
start_worker() {
    local service=$1
    local interval=$2
    
    echo -e "${GREEN}Starting ${service} worker (interval: ${interval}s)...${NC}"
    
    # Start in background, redirect output to logs
    nohup python3 scripts/pat_sync_worker.py \
        --service=$service \
        --interval=$interval \
        >> logs/${service}-worker.log 2>&1 &
    
    local pid=$!
    echo -e "${GREEN}  Started with PID: ${pid}${NC}"
    echo $pid
}

# Kill existing workers (if any)
echo "Cleaning up existing workers..."

# Find and kill existing python processes running pat_sync_worker.py
PIDS=$(pgrep -f "python3.*pat_sync_worker.py" || true)

if [ -n "$PIDS" ]; then
    echo -e "${YELLOW}Stopping existing workers...${NC}"
    for PID in $PIDS; do
        kill $PID 2>/dev/null
        echo -e "${YELLOW}  Stopped PID: ${PID}${NC}"
    done
    sleep 1
fi

# Start workers
echo ""
echo "Starting new workers..."
CALENDAR_PID=$(start_worker "calendar" "3600")
EMAIL_PID=$(start_worker "email" "300")
REMINDERS_PID=$(start_worker "reminders" "600")

# Save PIDs for cleanup
echo "$CALENDAR_PID" > .calendar-worker.pid
echo "$EMAIL_PID" > .email-worker.pid
echo "$REMINDERS_PID" > .reminders-worker.pid

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  All workers started!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Workers:"
echo "  - Calendar:  PID $CALENDAR_PID  (every 1 hour)"
echo "  - Email:     PID $EMAIL_PID     (every 5 minutes)"
echo "  - Reminders: PID $REMINDERS_PID (every 10 minutes)"
echo ""
echo "Logs:"
echo "  - Calendar:   logs/calendar-worker.log"
echo "  - Email:      logs/email-worker.log"
echo "  - Reminders: logs/reminders-worker.log"
echo "  - Combined:   logs/sync_workers.log"
echo ""
echo "Status check:"
echo "  Run: pgrep -f pat_sync_worker.py"
echo ""
echo "Stop all workers:"
echo "  ./scripts/stop_sync_workers.sh"
echo "  Or: pkill -f pat_sync_worker.py"
echo ""
echo "Log monitoring:"
echo "  tail -f logs/sync_workers.log"
echo ""
echo "Single worker test:"
echo "  python3 scripts/pat_sync_worker.py --service=calendar --once"
echo "  python3 scripts/pat_sync_worker.py --service=email --once"
echo "  python3 scripts/pat_sync_worker.py --service=reminders --once"
echo ""