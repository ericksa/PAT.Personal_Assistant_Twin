# src/main_pat.py - PAT Core API Entry Point
import uvicorn
import os
import logging

# Import the app factory function
from src.api.pat_routes import router as pat_router
from src.config.logging_config import setup_logging

# Set up structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_format = (
    "json" if os.getenv("ENVIRONMENT", "development") == "production" else "text"
)

setup_logging(service_name="pat-core", log_level=log_level, log_format=log_format)

logger = logging.getLogger(__name__)

# Create FastAPI app
from fastapi import FastAPI

app = FastAPI(
    title="PAT Core API - Personal Assistant Twin",
    description="""
    Personal Assistant Twin (PAT) Core API for:
    - Calendar Management with AI optimization
    - Email Processing with Llama 3.2 3B
    - Task Management with automation
    - Apple Calendar/Mail/Reminders integration
    - AI-powered predictions and suggestions
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Include PAT routes
app.include_router(pat_router)

# CORS for frontend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("PAT Core API initialized with Llama 3.2 3B")

if __name__ == "__main__":
    logger.info("Starting PAT Core API")

    port = int(os.getenv("PAT_PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
