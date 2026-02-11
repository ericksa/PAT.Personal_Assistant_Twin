#!/bin/bash

# Build and run PAT Overlay app

echo "Building PAT Overlay app..."

# Create build directory
mkdir -p build

# Build the app
swift build --product PATOverlay -c release

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "To run the app:"
    echo "  cd build/debug"
    echo "  open PATOverlay.app"
else
    echo "Build failed!"
fi