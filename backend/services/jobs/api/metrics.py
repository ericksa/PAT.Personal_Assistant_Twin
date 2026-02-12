# services/jobs/api/metrics.py - Prometheus Metrics Endpoint
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import APIRouter, Response
import logging
import time

logger = logging.getLogger("metrics")

# Create router for metrics endpoints
metrics_router = APIRouter()

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_inprogress = Gauge(
    "http_requests_inprogress",
    "Number of HTTP requests currently in progress",
    ["method"],
)

# Application Info
app_info = Info("job_search_service", "Job Search Service information")


def initialize_metrics(version: str = "1.0.0", environment: str = "development"):
    """Initialize application info metrics"""
    app_info.info(
        {
            "version": version,
            "environment": environment,
            "service": "job-search-service",
        }
    )


@metrics_router.get("/metrics", tags=["System"])
async def metrics():
    """
    Prometheus metrics endpoint
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@metrics_router.get("/health_metrics", tags=["System"])
async def health_metrics():
    """
    Health check endpoint for metrics service
    """
    return {"status": "healthy", "service": "job-search-metrics"}
