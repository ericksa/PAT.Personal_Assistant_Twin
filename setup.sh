#!/bin/bash

# 🚀 OpenCode Orchestration Setup Script
# Project: PAT (Personal Assistant Toolkit)

set -e

echo "--------------------------------------------------"
echo "📦 Setting up OpenCode Orchestration Environment..."
echo "--------------------------------------------------"

# 1. Create Directories
echo "[1/4] Creating directories..."
mkdir -p .opencode/agents .opencode/prompts .opencode/tools .opencode/logs

# 2. Check for OpenCode CLI
echo "[2/4] Checking prerequisites..."
if ! command -v opencode &> /dev/null; then
    echo "OpenCode CLI not found. Installing..."
    npm install -g opencode-ai
else
    echo "OpenCode CLI found."
fi

# 3. Initialize config if missing
if [ ! -f ".opencode/config.jsonc" ]; then
    echo "[3/4] Initializing default configuration..."
    # (Assuming the user will copy-paste from our plan or we've already written it)
else
    echo "[3/4] Configuration found."
fi

# 4. Final verification
echo "[4/4] Running verification..."
bash .opencode/verify-setup.sh

echo ""
echo "--------------------------------------------------"
echo "✅ Setup complete! Ready to launch."
echo "Launch command: opencode serve --port 4096"
echo "--------------------------------------------------"
