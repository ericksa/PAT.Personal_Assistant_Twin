# src/config/logging_config.py - Structured Logging Configuration
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
from pythonjsonlogger import jsonlogger
import os


def setup_logging(
    service_name: str = "job-search-service",
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """
    Configure structured logging for the application.

    Args:
        service_name: Name of the service for log tagging
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type - 'json' for production, 'text' for development
    """

    # Create logs directory if it doesn't exist
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)

    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s",
        timestamp=True,
    )

    # Text formatter for development
    text_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handlers configuration
    handlers: Dict[str, Any] = {
        "console": {
            "()": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json" if log_format == "json" else "text",
        },
        "file_info": {
            "()": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "info.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,  # Keep 5 backup files (30 days retention total)
            "formatter": "json" if log_format == "json" else "text",
            "level": "INFO",
        },
        "file_error": {
            "()": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "error.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,  # Keep 5 backup files (30 days retention total)
            "formatter": "json" if log_format == "json" else "text",
            "level": "ERROR",
        },
    }

    # Loggers configuration
    loggers: Dict[str, Any] = {
        "": {  # Root logger
            "level": log_level,
            "handlers": ["console", "file_info", "file_error"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console", "file_info"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
    }

    # Formatters
    formatters: Dict[str, Any] = {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s",
        },
        "text": {
            "()": "logging.Formatter",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }

    # Logging configuration
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": loggers,
    }

    logging.config.dictConfig(logging_config)

    # Log initialization
    logger = logging.getLogger(service_name)
    logger.info(
        f"Logging initialized for {service_name}",
        extra={
            "service": service_name,
            "level": log_level,
            "format": log_format,
            "version": "1.0.0",
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically the module name)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """Helper class for logging HTTP requests with structured data"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("requests")

    def log_request(
        self, method: str, path: str, status_code: int, duration_ms: float, **kwargs
    ):
        """Log an HTTP request with structured data"""
        self.logger.info(
            "HTTP Request",
            extra={
                "event": "http_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                **kwargs,
            },
        )

    def log_error(self, method: str, path: str, error: str, **kwargs):
        """Log an HTTP error with structured data"""
        self.logger.error(
            "HTTP Error",
            extra={
                "event": "http_error",
                "method": method,
                "path": path,
                "error": error,
                **kwargs,
            },
        )


class BusinessLogger:
    """Helper class for logging business events with structured data"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("business")

    def log_job_search(
        self,
        keywords: str,
        location: str,
        jobs_found: int,
        duration_ms: float,
        **kwargs,
    ):
        """Log a job search event"""
        self.logger.info(
            "Job Search Executed",
            extra={
                "event": "job_search",
                "keywords": keywords,
                "location": location,
                "jobs_found": jobs_found,
                "duration_ms": round(duration_ms, 2),
                **kwargs,
            },
        )

    def log_job_alert(self, job_count: int, success: bool, **kwargs):
        """Log an email alert event"""
        self.logger.info(
            "Email Alert Sent",
            extra={
                "event": "email_alert",
                "job_count": job_count,
                "success": success,
                **kwargs,
            },
        )

    def log_scheduler_run(
        self, jobs_found: int, high_quality_count: int, duration_ms: float, **kwargs
    ):
        """Log a scheduler run event"""
        self.logger.info(
            "Scheduler Run Completed",
            extra={
                "event": "scheduler_run",
                "jobs_found": jobs_found,
                "high_quality_count": high_quality_count,
                "duration_ms": round(duration_ms, 2),
                **kwargs,
            },
        )

    def log_error(self, operation: str, error_message: str, **kwargs):
        """Log a business error"""
        self.logger.error(
            "Operation Error",
            extra={
                "event": "operation_error",
                "operation": operation,
                "error_message": error_message,
                **kwargs,
            },
        )
