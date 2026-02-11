"""
PAT Core Service - Personal Assistant Twin
Main entry point for the PAT Core API service
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

import uvicorn
from fastapi import FastAPI
from api.pat_routes import router as pat_router
from config.logging_config import setup_logging

setup_logging(service_name="pat-core", log_level="INFO", log_format="text")

app = FastAPI(
    title="PAT Core API",
    description="Personal Assistant Twin - Calendar, Email, Task Management with Llama 3.2 3B",
    version="1.0.0",
)

app.include_router(pat_router)

if __name__ == "__main__":
    uvicorn.run(
        "main_pat:app", host="0.0.0.0", port=8010, reload=True, log_level="info"
    )
