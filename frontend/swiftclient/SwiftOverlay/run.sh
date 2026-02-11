#!/bin/bash

# Run PAT Overlay app

echo "Starting PAT Overlay app..."

# Build if needed
if [ ! -f .build/debug/PATOverlay ]; then
    echo "Building PAT Overlay app..."
    swift build --product PATOverlay -c debug
fi

# Run the app
if [ -f .build/debug/PATOverlay ]; then
    echo "Launching PAT Overlay..."
    .build/debug/PATOverlay
else
    echo "Failed to build PAT Overlay app"
fi