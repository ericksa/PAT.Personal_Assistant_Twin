# src/main.py - Application Entry Point
import uvicorn
import os
import logging

# Import configurations
from src.config.logging_config import setup_logging
from src.config.app_settings import settings

# Import the app factory function
from src.api.opportunity_routes import create_app
from src.api.metrics_routes import metrics_router, initialize_metrics

# Import middleware
from src.utils.logging_middleware import LoggingMiddleware
from src.utils.metrics_middleware import MetricsMiddleware


def main():
    """Main entry point for the application"""

    # Set up structured logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = (
        "json" if os.getenv("ENVIRONMENT", "development") == "production" else "text"
    )

    setup_logging(
        service_name="job-search-service", log_level=log_level, log_format=log_format
    )

    logger = logging.getLogger("main")
    logger.info(
        "Starting PAT Job Search Service",
        extra={
            "version": settings.VERSION,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": log_level,
        },
    )

    # Create the FastAPI application
    app = create_app()

    # Initialize metrics
    initialize_metrics(
        version=settings.VERSION, environment=os.getenv("ENVIRONMENT", "development")
    )

    # Add metrics router
    app.include_router(metrics_router)

    # Add middleware (order matters - logging first, then metrics)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware)

    # Log startup
    logger.info(
        "Application initialized and ready",
        extra={
            "port": int(os.getenv("PORT", "8007")),
            "metrics_available": True,
            "docs_url": "/docs",
            "redoc_url": "/redoc",
        },
    )

    # Run with uvicorn
    port = int(os.getenv("PORT", "8007"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_config=None,  # Use our custom logging setup
    )


if __name__ == "__main__":
    main()
