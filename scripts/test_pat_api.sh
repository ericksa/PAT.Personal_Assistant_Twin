#!/bin/bash
# PAT Core API Test Suite
# Automated testing of all PAT Core endpoints

BASE_URL="http://localhost:8010"
passed=0
failed=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_test() {
    local test_name=$1
    local result=$2
    
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        ((passed++))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        ((failed++))
    fi
}

echo "========================================="
echo "  PAT Core API Test Suite"
echo "========================================="
echo "Testing: $BASE_URL"
echo ""

echo "========================================="
echo "  System Tests"
echo "========================================="

# Test 1: Health Check
curl -s -f "${BASE_URL}/pat/health" > /dev/null 2>&1
log_test "Health Check" $?

# Test 2: Info Endpoint
curl -s -f "${BASE_URL}/pat/info" > /dev/null 2>&1
log_test "Info Endpoint" $?

# Test 3: LLM Connection Test
curl -s -f "${BASE_URL}/pat/chat/test-connection" > /dev/null 2>&1
log_test "LLM Connection Test" $?

echo ""
echo "========================================="
echo "  Calendar Tests"
echo "========================================="

# Test 4: Create Calendar Event
EVENT_RESPONSE=$(curl -s -X POST "${BASE_URL}/pat/calendar/events" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Meeting from Test Suite",
    "description": "Automated test event",
    "start_date": "2026-02-12",
    "start_time": "14:00",
    "end_date": "2026-02-12",
    "end_time": "15:00",
    "location": "Test Location",
    "event_type": "meeting"
  }' 2>&1)

if echo "$EVENT_RESPONSE" | grep -q '"status":"success"'; then
    log_test "Create Calendar Event" 0
    
    # Extract event ID
    EVENT_ID=$(echo "$EVENT_RESPONSE" | jq -r '.event.id' 2>/dev/null || echo "")
    
    if [ -n "$EVENT_ID" ] && [ "$EVENT_ID" != "null" ]; then
        # Test 5: Get Single Event
        curl -s -f "${BASE_URL}/pat/calendar/events/${EVENT_ID}" > /dev/null 2>&1
        log_test "Get Calendar Event" $?
    else
        log_test "Create Calendar Event" 1
    fi
else
    log_test "Create Calendar Event" 1
fi

# Test 6: List Calendar Events
curl -s -f "${BASE_URL}/pat/calendar/events?limit=10" > /dev/null 2>&1
log_test "List Calendar Events" $?

# Test 7: Sync from Apple Calendar
curl -s -f "${BASE_URL}/pat/calendar/sync?calendar_name=PAT-cal&hours_back=72" > /dev/null 2>&1
log_test "Sync Apple Calendar" $?

echo ""
echo "========================================="
echo "  Task Tests"
echo "========================================="

# Test 8: Create Task
TASK_RESPONSE=$(curl -s -X POST "${BASE_URL}/pat/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task from Test Suite",
    "description": "Automated test task",
    "priority": "high",
    "tags": ["test", "automation"]
  }' 2>&1)

if echo "$TASK_RESPONSE" | grep -q '"status":"success"'; then
    log_test "Create Task" 0
    
    # Extract task ID
    TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.task.id' 2>/dev/null || echo "")
    
    if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
        # Test 9: Get Single Task
        curl -s -f "${BASE_URL}/pat/tasks/${TASK_ID}" > /dev/null 2>&1
        log_test "Get Task" $?
        
        # Test 10: Complete Task
        COMPLETE_RESPONSE=$(curl -s -X POST "${BASE_URL}/pat/tasks/${TASK_ID}/complete" \
          -H "Content-Type: application/json" \
          -d '{"notes": "Automated test completion"}' 2>&1)
        
        if echo "$COMPLETE_RESPONSE" | grep -q '"status":"success"'; then
            log_test "Complete Task" 0
        else
            log_test "Complete Task" 1
        fi
    else
        log_test "Create Task" 1
    fi
else
    log_test "Create Task" 1
fi

# Test 11: List Tasks
curl -s -f "${BASE_URL}/pat/tasks" > /dev/null 2>&1
log_test "List Tasks" $?

# Test 12: Get Focus Tasks
curl -s -f "${BASE_URL}/pat/tasks/focus" > /dev/null 2>&1
log_test "Get Focus Tasks" $?

echo ""
echo "========================================="
echo "  Email AI Tests (Text-based)"
echo "========================================="

# Test 13: Classify Email
curl -s -f "${BASE_URL}/pat/emails/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Urgent: Project Deadline Tomorrow",
    "sender": "manager@company.com",
    "body": "Please ensure the quarterly report is submitted by EOD tomorrow."
  }' > /dev/null 2>&1
log_test "Classify Email" $?

# Test 14: Summarize Email
curl -s -f "${BASE_URL}/pat/emails/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Q1 Budget Review",
    "body": "We need to review the Q1 budget allocations across all departments."
  }' > /dev/null 2>&1
log_test "Summarize Email" $?

# Test 15: Draft Email Reply
curl -s -f "${BASE_URL}/pat/emails/draft-reply" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Meeting Rescheduling",
    "sender": "client@business.com",
    "body": "Can we move our meeting from Tuesday to Thursday?",
    "tone": "professional"
  }' > /dev/null 2>&1
log_test "Draft Email Reply" $?

# Test 16: Extract Tasks from Text
curl -s -f "${BASE_URL}/pat/emails/extract-tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Remember to update the project timeline and send meeting notes to attendees."
  }' > /dev/null 2>&1
log_test "Extract Tasks from Text" $?

# Test 17: Extract Meeting from Text
curl -s -f "${BASE_URL}/pat/emails/extract-meeting" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Let\'s have a sync tomorrow at 2 PM for one hour in Conference Room B."
  }' > /dev/null 2>&1
log_test "Extract Meeting from Text" $?

echo ""
echo "========================================="
echo "  Chat/LLM Tests"
echo "========================================="

# Test 18: Chat Completion
curl -s -f "${BASE_URL}/pat/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are 3 tips for effective time management?"}
    ]
  }' > /dev/null 2>&1
log_test "Chat Completion" $?

echo ""
echo "========================================="
echo "  Test Results Summary"
echo "========================================="
echo ""
echo -e "Tests Passed: ${GREEN}${passed}${NC}"
echo -e "Tests Failed: ${RED}${failed}${NC}"
echo -e "Total Tests: $((passed + failed))"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  ALL TESTS PASSED!  🎉${NC}"
    echo -e "${GREEN}=========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  SOME TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi