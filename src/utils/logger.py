"""
Logging utilities for AWS Content Monitor.
"""
import logging
import os
import sys
from datetime import datetime


def setup_logger(name: str = "aws-content-monitor", level: str = None) -> logging.Logger:
    """Set up structured logging for the application."""
    
    # Get log level from environment or default to INFO
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    log_file = os.environ.get("LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_execution_metrics(logger: logging.Logger, metrics: dict) -> None:
    """Log execution metrics in a structured format."""
    logger.info("Execution Metrics", extra={"metrics": metrics})


def log_error_with_context(logger: logging.Logger, error: Exception, context: dict = None) -> None:
    """Log error with additional context information."""
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }
    
    if context:
        error_info.update(context)
    
    logger.error("Error occurred", extra={"error_info": error_info})