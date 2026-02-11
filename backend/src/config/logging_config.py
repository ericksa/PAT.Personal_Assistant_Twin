import logging
import logging.config
import os
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
        "": {
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

    def log_pat_event(self, event_type: str, duration_ms: float, **kwargs):
        """Log a PAT core event"""
        self.logger.info(f"PAT Event: {event_type} ({duration_ms:.0f}ms)")

    def log_ai_request(self, model: str, operation: str, duration_ms: float, **kwargs):
        """Log an AI request event"""
        self.logger.info(f"AI Request: {model} - {operation} ({duration_ms:.0f}ms)")

    def log_sync_event(
        self,
        source: str,
        operation: str,
        items_count: int,
        duration_ms: float,
        **kwargs,
    ):
        """Log a sync event"""
        self.logger.info(
            f"Sync: {source} - {operation} ({items_count} items, {duration_ms:.0f}ms)"
        )

    def log_error(self, operation: str, error_message: str, **kwargs):
        """Log a business error"""
        self.logger.error(f"Operation Error ({operation}): {error_message}")
