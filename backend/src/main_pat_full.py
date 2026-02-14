#!/usr/bin/env python3
"""
PAT Core API Entry Point - Full Implementation
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.pat_routes import router as pat_router

app = FastAPI(
    title="PAT Core API - Personal Assistant Twin",
    description="""
    Personal Assistant Twin (PAT) Core API for:
    - Calendar Management with AI optimization
    - Email Processing with AI classification
    - Task Management with automation
    - AI-powered chat completions
    - Unified analytics across all services
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Include PAT routes
app.include_router(pat_router)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("PAT Core API initialized with full route support")


if __name__ == "__main__":
    logger.info("Starting PAT Core API with full features")

    port = int(os.getenv("PAT_PORT", "8010"))
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
