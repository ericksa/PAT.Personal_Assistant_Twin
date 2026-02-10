#!/bin/bash

cd /Users/adamerickson/Projects/PAT/SwiftOverlay

echo "🐢 Starting PATOverlay..."
open PATOverlay.app
# Give it time to start
echo "⏳ Waiting for app to initialize..."
sleep 3

echo "📡 Testing WebSocket connection..."

# Send test message to teleprompter
echo "📝 Sending test message to teleprompter service..."
curl -X POST http://localhost:8005/broadcast \
  -H "Content-Type: application/json" \
  -d '{"message": "SwiftOverlay integration test: Hello from macOS overlay!"}'

echo -e "\n✅ Test completed. Check if the SwiftOverlay window displays the test message."
echo "   - Look for a floating transparent window with 'SwiftOverlay integration test'"