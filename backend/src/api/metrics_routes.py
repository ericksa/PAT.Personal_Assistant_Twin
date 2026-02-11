# src/api/metrics_routes.py - Prometheus Metrics Endpoint
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
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


# Business Metrics
job_searches_total = Counter(
    "job_searches_total", "Total job searches performed", ["location", "success"]
)

jobs_found_total = Histogram(
    "jobs_found_total",
    "Number of jobs found per search",
    buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500],
)

job_alerts_sent_total = Counter(
    "job_alerts_sent_total", "Total email alerts sent", ["success"]
)

high_quality_jobs_found_total = Counter(
    "high_quality_jobs_found_total", "Total high-quality job matches found"
)


# Scheduler Metrics
scheduler_runs_total = Counter(
    "scheduler_runs_total", "Total scheduler runs completed", ["success"]
)

scheduler_last_run_timestamp = Gauge(
    "scheduler_last_run_timestamp", "Timestamp of the last scheduler run"
)


# Database Metrics
database_operations_total = Counter(
    "database_operations_total",
    "Total database operations",
    ["operation", "table", "success"],
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5, 1.0, 5.0],
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

    Exposes metrics in Prometheus format for scraping.
    Includes HTTP request metrics, business metrics, and system metrics.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@metrics_router.get("/health", tags=["System"])
async def health():
    """
    Health check endpoint for metrics service

    Simple health check to verify metrics endpoint is accessible.
    """
    return {"status": "healthy", "service": "job-search-metrics"}


# Helper classes for tracking metrics


class MetricsHelper:
    """Helper class to easily track business metrics"""

    @staticmethod
    def track_job_search(
        success: bool, location: str, jobs_found: int, high_quality: int = 0
    ):
        """Track a job search operation"""
        job_searches_total.labels(
            location=location, success="true" if success else "false"
        ).inc()

        if success:
            jobs_found_total.observe(jobs_found)
            high_quality_jobs_found_total.inc(high_quality)

    @staticmethod
    def track_email_alert(success: bool, job_count: int):
        """Track an email alert operation"""
        job_alerts_sent_total.labels(success="true" if success else "false").inc()

    @staticmethod
    def track_scheduler_run(success: bool):
        """Track a scheduler run"""
        scheduler_runs_total.labels(success="true" if success else "false").inc()
        scheduler_last_run_timestamp.set_to_current_time()

    @staticmethod
    def track_database_operation(
        operation: str, table: str, success: bool, duration_seconds: float
    ):
        """Track a database operation"""
        database_operations_total.labels(
            operation=operation, table=table, success="true" if success else "false"
        ).inc()
        database_query_duration_seconds.labels(
            operation=operation, table=table
        ).observe(duration_seconds)


# Context manager for HTTP request duration tracking
class RequestDurationContext:
    """Context manager for tracking HTTP request duration"""

    def __init__(self, method: str, endpoint: str, status_code_func):
        self.method = method
        self.endpoint = endpoint
        self.status_code_func = status_code_func
        self.start_time = None

    def __enter__(self):
        http_requests_inprogress.labels(method=self.method).inc()
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        http_requests_inprogress.labels(method=self.method).dec()

        # Get status code
        status_code = self.status_code_func() if self.status_code_func else 500

        # Record metrics
        http_requests_total.labels(
            method=self.method, endpoint=self.endpoint, status_code=str(status_code)
        ).inc()

        http_request_duration_seconds.labels(
            method=self.method, endpoint=self.endpoint
        ).observe(duration)
