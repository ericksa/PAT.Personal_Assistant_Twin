# src/utils/logging_middleware.py - Logging Middleware for FastAPI
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from src.config.logging_config import RequestLogger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses with structured data"""

    def __init__(
        self, app: ASGIApp, logger: logging.Logger = None, log_level: str = "INFO"
    ):
        super().__init__(app)
        self.logger = logger or logging.getLogger("api")
        self.log_level = log_level
        self.request_logger = RequestLogger(logger or logging.getLogger("requests"))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""

        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Get client info
        client_host = request.client.host if request.client else "unknown"
        client_port = request.client.port if request.client else 0

        # Start timing
        start_time = time.time()

        # Log request
        self.logger.info(
            "Incoming request",
            extra={
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": client_host,
                "client_port": client_port,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            self.request_logger.log_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                client_host=client_host,
                client_port=client_port,
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration for error case
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            self.request_logger.log_error(
                method=request.method,
                path=request.url.path,
                error=str(e),
                request_id=request_id,
                duration_ms=duration_ms,
            )

            # Re-raise the exception
            raise


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs"""

    SENSITIVE_FIELDS = {
        "password",
        "token",
        "api_key",
        "secret",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "session_id",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log records"""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._redact_data(record.msg)

        if hasattr(record, "args"):
            record.args = tuple(
                self._redact_data(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )

        # Redact sensitive fields in extra dict
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            self._redact_dict(record.extra_data)

        return True

    def _redact_data(self, data: str) -> str:
        """Redact sensitive data from string"""
        redacted = data
        for field in self.SENSITIVE_FIELDS:
            # Simple pattern matching - in production, use more sophisticated parsing
            pattern = f'"{field}"\\s*:\\s*"([^"]*)"'
            redacted = __import__("re").sub(
                pattern,
                f'"{field}": "[REDACTED]"',
                redacted,
                flags=__import__("re").IGNORECASE,
            )
        return redacted

    def _redact_dict(self, data: dict):
        """Redact sensitive values from dictionary"""
        for key in list(data.keys()):
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                data[key] = "[REDACTED]"
            elif isinstance(data[key], dict):
                self._redact_dict(data[key])
