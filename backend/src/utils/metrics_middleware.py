# src/utils/metrics_middleware.py - Prometheus Metrics Middleware for FastAPI
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from src.api.metrics_routes import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_inprogress,
)
from src.api.metrics_routes import MetricsHelper


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics using Prometheus"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("api")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track metrics"""

        # Track in-progress request
        try:
            http_requests_inprogress.labels(method=request.method).inc()

            # Start timer
            start_time = time.time()

            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics on success
            endpoint = self._get_route_name(request)
            status_code = response.status_code

            http_requests_total.labels(
                method=request.method, endpoint=endpoint, status_code=str(status_code)
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            # Log slow requests
            if duration > 5.0:
                self.logger.warning(
                    f"Slow request detected",
                    extra={
                        "event": "slow_request",
                        "method": request.method,
                        "path": request.url.path,
                        "endpoint": endpoint,
                        "duration_seconds": round(duration, 2),
                        "status_code": status_code,
                    },
                )

            return response

        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time if "start_time" in locals() else 0

            # Record error metrics
            endpoint = self._get_route_name(request)

            http_requests_total.labels(
                method=request.method, endpoint=endpoint, status_code="500"
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            # Log error
            self.logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "event": "request_error",
                    "method": request.method,
                    "path": request.url.path,
                    "endpoint": endpoint,
                    "duration_seconds": round(duration, 2),
                    "error": str(e),
                },
            )

            # Re-raise the exception
            raise

        finally:
            # Always decrement in-progress counter
            http_requests_inprogress.labels(method=request.method).dec()

    def _get_route_name(self, request: Request) -> str:
        """
        Get the route name from the request.

        Try to extract the route pattern, otherwise use the path.
        """
        try:
            if hasattr(request, "route") and request.route:
                return f"{request.route.path}"
            return request.url.path
        except Exception:
            return request.url.path


class BusinessMetricsTracker:
    """Helper class for tracking business-specific metrics"""

    def __init__(self):
        self.logger = logging.getLogger("business")
        self.metrics_helper = MetricsHelper()

    def track_opportunity_search(
        self,
        success: bool,
        location: str,
        opportunities_found: int,
        high_quality_count: int = 0,
        duration_ms: float = 0,
    ):
        """Track a job search operation with metrics and logging"""

        # Track Prometheus metrics
        self.metrics_helper.track_job_search(
            success=success,
            location=location,
            jobs_found=opportunities_found,
            high_quality=high_quality_count,
        )

        # Log business event
        self.logger.info(
            "Opportunity Search Completed",
            extra={
                "event": "opportunity_search",
                "success": success,
                "location": location,
                "opportunities_found": opportunities_found,
                "high_quality_count": high_quality_count,
                "duration_ms": round(duration_ms, 2),
            },
        )

    def track_email_alert(
        self, success: bool, job_count: int, recipient: str = "unknown"
    ):
        """Track an email alert operation"""

        # Track Prometheus metrics
        self.metrics_helper.track_email_alert(success=success, job_count=job_count)

        # Log business event
        if success:
            self.logger.info(
                "Email Alert Sent Successfully",
                extra={
                    "event": "email_alert_sent",
                    "recipient": recipient,
                    "job_count": job_count,
                },
            )
        else:
            self.logger.error(
                "Email Alert Failed",
                extra={
                    "event": "email_alert_failed",
                    "recipient": recipient,
                    "job_count": job_count,
                },
            )

    def track_scheduler_run(
        self,
        success: bool,
        duration_ms: float,
        jobs_found: int = 0,
        high_quality_count: int = 0,
    ):
        """Track a scheduled search run"""

        # Track Prometheus metrics
        self.metrics_helper.track_scheduler_run(success=success)

        # Log business event
        self.logger.info(
            "Scheduler Run Completed",
            extra={
                "event": "scheduler_run",
                "success": success,
                "duration_ms": round(duration_ms, 2),
                "jobs_found": jobs_found,
                "high_quality_count": high_quality_count,
            },
        )

    def track_database_operation(
        self,
        operation: str,
        table: str,
        success: bool,
        duration_seconds: float,
        rows_affected: int = None,
    ):
        """Track a database operation"""

        # Track Prometheus metrics
        self.metrics_helper.track_database_operation(
            operation=operation,
            table=table,
            success=success,
            duration_seconds=duration_seconds,
        )

        # Log slow database operations
        if duration_seconds > 1.0:
            self.logger.warning(
                "Slow Database Operation",
                extra={
                    "event": "slow_db_operation",
                    "operation": operation,
                    "table": table,
                    "duration_seconds": round(duration_seconds, 2),
                    "rows_affected": rows_affected,
                },
            )
