"""
Centralized logging configuration for the application
Provides structured logging with proper formatting and handlers
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from contextvars import ContextVar

# Context variable to store user_id across async calls
user_context: ContextVar[int] = ContextVar('user_id', default=None)


# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class UserContextFilter(logging.Filter):
    """Logging filter that adds user_id to log records"""

    def filter(self, record):
        user_id = user_context.get()
        record.user_id = user_id if user_id else 'Anonymous'
        return True


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - [User:%(user_id)s] - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: blue + "%(asctime)s - [User:%(user_id)s] - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - [User:%(user_id)s] - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - [User:%(user_id)s] - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - [User:%(user_id)s] - %(name)s - %(levelname)s - %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "app.log",
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 5
):
    """
    Setup application-wide logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add user context filter to all handlers
    user_filter = UserContextFilter()

    # Console Handler (with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomFormatter())
    console_handler.addFilter(user_filter)
    root_logger.addHandler(console_handler)

    # File Handler (rotating, detailed)
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - [User:%(user_id)s] - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(user_filter)
    root_logger.addHandler(file_handler)

    # Error File Handler (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "error.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    error_handler.addFilter(user_filter)
    root_logger.addHandler(error_handler)

    # API Request Handler (for API-specific logs)
    api_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "api.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(file_formatter)
    api_handler.addFilter(user_filter)

    # Add handler to API logger
    api_logger = logging.getLogger("app.api")
    api_logger.addHandler(api_handler)

    # Celery Task Handler
    celery_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "celery.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    celery_handler.setLevel(logging.INFO)
    celery_handler.setFormatter(file_formatter)
    celery_handler.addFilter(user_filter)

    # Add handler to celery logger
    celery_logger = logging.getLogger("app.tasks")
    celery_logger.addHandler(celery_handler)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)

    root_logger.info("Logging system initialized")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Log files: {LOGS_DIR}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience functions for structured logging
def log_api_request(logger: logging.Logger, method: str, path: str, user_id: int = None):
    """Log API request"""
    logger.info(f"API Request: {method} {path} | User: {user_id or 'Anonymous'}")


def log_api_response(logger: logging.Logger, method: str, path: str, status_code: int, duration: float):
    """Log API response"""
    logger.info(f"API Response: {method} {path} | Status: {status_code} | Duration: {duration:.3f}s")


def log_task_start(logger: logging.Logger, task_name: str, **kwargs):
    """Log task start"""
    params = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"Task Started: {task_name} | {params}")


def log_task_complete(logger: logging.Logger, task_name: str, duration: float, **kwargs):
    """Log task completion"""
    params = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"Task Completed: {task_name} | Duration: {duration:.3f}s | {params}")


def log_task_error(logger: logging.Logger, task_name: str, error: Exception, **kwargs):
    """Log task error"""
    params = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.error(f"Task Failed: {task_name} | Error: {str(error)} | {params}", exc_info=True)


def set_user_context(user_id: int):
    """
    Set the user_id in the current context for logging

    Args:
        user_id: User ID to set in context
    """
    user_context.set(user_id)


def clear_user_context():
    """Clear the user_id from the current context"""
    user_context.set(None)
