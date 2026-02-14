# src/main_pat.py - PAT Core API Entry Point (Minimal Working Version)
import uvicorn
import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PAT Core API - Personal Assistant Twin",
    description="""
    Personal Assistant Twin (PAT) Core API for:
    - Calendar Management with AI optimization
    - Email Processing with GLM-4.6v-flash
    - Task Management with automation
    - AI-powered predictions and suggestions
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Create basic router
router = APIRouter(prefix="/pat")


# Basic health endpoint
@router.get("/health")
async def pat_health():
    """Health check for PAT Core API"""
    return {
        "status": "healthy",
        "service": "pat-core",
        "features": {"calendar": True, "email": True, "tasks": True, "ai": True},
        "model": "glm-4.6v-flash",
    }


# Basic analytics endpoint
@router.get("/analytics")
async def pat_analytics():
    """Basic analytics endpoint"""
    return {
        "status": "healthy",
        "analytics": {
            "total_emails": 0,
            "total_tasks": 0,
            "upcoming_events": 0,
            "recent_activities": 0,
        },
    }


# Include PAT routes
app.include_router(router)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("PAT Core API initialized with GLM-4.6v-flash support")

if __name__ == "__main__":
    logger.info("Starting PAT Core API")

    port = int(os.getenv("PAT_PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
