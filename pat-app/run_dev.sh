#!/bin/bash

# Exit on error and print commands
set -ex

# Install dependencies if needed
if [ ! -d "pat-app/backend/.venv" ]; then
    cd pat-app/backend
    poetry install
    cd - > /dev/null
fi

# Run the FastAPI server
cd pat-app/backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd - > /dev/null