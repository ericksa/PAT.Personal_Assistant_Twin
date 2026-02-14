#!/bin/bash
# Development server startup script for PAT Backend

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install it first:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ] && [ ! -d "$(poetry env info --path 2>/dev/null)" ]; then
    echo "Installing dependencies..."
    poetry install
fi

# Set environment variables
export ENVIRONMENT="development"
export DEBUG="true"
export LOG_LEVEL="INFO"

# Function to handle cleanup
cleanup() {
    echo "Shutting down server..."
    kill -TERM $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Start the server
echo "Starting PAT Backend API Development Server..."
echo "Server will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/api/v1/health/"
echo ""
echo "Press Ctrl+C to stop the server"

# Start uvicorn with auto-reload
poetry run uvicorn app.main:create_app --host 0.0.0.0 --port 8000 --reload &

SERVER_PID=$!
wait $SERVER_PID