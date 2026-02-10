#!/bin/bash

cd /Users/adamerickson/Projects/PAT/SwiftOverlay

# Build the app
echo "Building PAT Overlay..."
swift build --product PATOverlay

# Run the app in background
echo "Starting PAT Overlay..."
.build/debug/PATOverlay &
OVERLAY_PID=$!

echo "PAT Overlay started with PID: $OVERLAY_PID"
echo "Checking if window appears..."

# Wait a moment for window to appear
sleep 3

# List windows to see if overlay appears
osascript -e "tell application \"System Events\" to get name of every window of every process"

# Wait for user input to kill the process
echo "Press Enter to stop the overlay..."
read -r

# Kill the overlay process
kill $OVERLAY_PID
echo "PAT Overlay stopped"