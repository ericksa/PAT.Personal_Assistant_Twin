import logging
import logging.config
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logging(
    service_name: str = "pat-service",
    log_level: str = "INFO",
    log_format: str = "text",
) -> None:
    """
    Configure structured logging for the application.

    Args:
        service_name: Name of the service for log tagging
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type - 'json' for production, 'text' for development
    """

    # Create logs directory if it doesn't exist
    backend_dir = Path(__file__).parent.parent.parent
    script_dir = backend_dir / "logs"

    if not script_dir.exists():
        script_dir.mkdir(exist_ok=True)

    # Handlers configuration
    handlers: Dict[str, Any] = {
        "console": {
            "()": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "text",
        },
        "file_info": {
            "()": "logging.handlers.RotatingFileHandler",
            "filename": str(script_dir / "info.log"),
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "text",
            "level": "INFO",
        },
        "file_error": {
            "()": "logging.handlers.RotatingFileHandler",
            "filename": str(script_dir / "error.log"),
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "text",
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
    logger.info(f"Logging initialized for {service_name} (level={log_level})")


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

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("requests")

    def log_request(
        self, method: str, path: str, status_code: int, duration_ms: float, **kwargs
    ):
        """Log an HTTP request with structured data"""
        self.logger.info(f"HTTP {method} {path} - {status_code} ({duration_ms:.0f}ms)")

    def log_error(self, method: str, path: str, error: str, **kwargs):
        """Log an HTTP error with structured data"""
        self.logger.error(f"HTTP Error: {method} {path} - {error}")


class BusinessLogger:
    """Helper class for logging business events with structured data"""

    def __init__(self, logger: Optional[logging.Logger] = None):
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
