"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import psutil
import time
from datetime import datetime, UTC
from typing import Dict, Any

# Import routers
from app.api.v1.health import router as health_router
from app.api.v1.items import router as items_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    startup_time = time.time()
    logger.info("Starting PAT Backend Application", extra={
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "log_level": settings.LOG_LEVEL
    })
    
    yield
    
    # Shutdown
    logger.info("Shutting down PAT Backend Application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="PAT Backend API",
        description="Personal Assistant Toolkit - Backend API Service",
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    app.include_router(items_router, prefix="/api/v1/items", tags=["items"])
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "PAT Backend API",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "running",
            "timestamp": datetime.now(UTC).isoformat(),
            "docs": "/docs" if settings.DEBUG else "disabled in production"
        }
    
    return app


# Global logger configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    uvicorn.run(
        "app.main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )