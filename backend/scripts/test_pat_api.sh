#!/bin/bash
# scripts/test_pat_api.sh - Automated test suite for PAT Core API

API_URL=${1:-"http://localhost:8010/pat"}
echo "Testing PAT Core API at $API_URL"

# 1. Health Check
echo -n "Checking health: "
curl -s "$API_URL/health" | grep -q "healthy" && echo "OK" || echo "FAILED"

# 2. LLM Connection
echo -n "Testing LLM connection: "
curl -s -X POST "$API_URL/chat/test-connection" | grep -q "success" && echo "OK" || echo "FAILED"

# 3. Create Calendar Event
echo -n "Creating calendar event: "
EVENT_ID=$(curl -s -X POST "$API_URL/calendar/events" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Test Event",
    "start_time": "'$(date -v+1d +"%Y-%m-%dT09:00:00")'",
    "end_time": "'$(date -v+1d +"%Y-%m-%dT10:00:00")'",
    "event_type": "meeting"
  }' | jq -r '.event.id')

if [ "$EVENT_ID" != "null" ] && [ -n "$EVENT_ID" ]; then
    echo "OK (ID: $EVENT_ID)"
else
    echo "FAILED"
fi

# 4. List Calendar Events
echo -n "Listing calendar events: "
curl -s "$API_URL/calendar/events" | jq -r '.count' | grep -q "^[0-9]" && echo "OK" || echo "FAILED"

# 5. List Emails
echo -n "Listing emails: "
curl -s "$API_URL/emails" | jq -r '.count' | grep -q "^[0-9]" && echo "OK" || echo "FAILED"

# 6. List Tasks
echo -n "Listing tasks: "
curl -s "$API_URL/tasks" | jq -r '.count' | grep -q "^[0-9]" && echo "OK" || echo "FAILED"

# 7. Sync Tasks (Dry run/Trigger)
echo -n "Triggering task sync: "
curl -s -X POST "$API_URL/tasks/sync?limit=1" | grep -q "Synced" && echo "OK" || echo "FAILED"

echo "API tests completed."
