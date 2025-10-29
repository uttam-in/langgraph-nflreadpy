"""
Logging Configuration for NFL Player Performance Chatbot.

This module provides centralized logging configuration with appropriate
log levels, formatters, and handlers for different components.

Requirements addressed:
- 7.3: Log errors with sufficient detail for debugging
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Default log levels for different components
DEFAULT_LOG_LEVELS = {
    "root": "INFO",
    "workflow": "INFO",
    "nodes": "INFO",
    "data_sources": "INFO",
    "error_handler": "INFO",
    "chainlit": "WARNING",
    "langgraph": "WARNING",
    "langchain": "WARNING",
    "openai": "WARNING",
    "httpx": "WARNING",
}


# Log format strings
DETAILED_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "[%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s"
)

SIMPLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

CONSOLE_FORMAT = "%(levelname)s - %(name)s - %(message)s"


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    console_output: bool = True,
    detailed_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """
    Configure logging for the chatbot application.
    
    Args:
        log_level: Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional specific log file name (default: auto-generated with timestamp)
        log_dir: Directory for log files
        console_output: Whether to output logs to console
        detailed_format: Whether to use detailed log format with file/line info
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Requirements:
        - 7.3: Configures logging with appropriate detail levels
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Determine log file name
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"chatbot_{timestamp}.log"
    
    log_file_path = log_path / log_file
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Choose format
    log_format = DETAILED_FORMAT if detailed_format else SIMPLE_FORMAT
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = logging.Formatter(CONSOLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Set specific log levels for different components
    for logger_name, level in DEFAULT_LOG_LEVELS.items():
        if logger_name != "root":
            component_logger = logging.getLogger(logger_name)
            component_logger.setLevel(getattr(logging, level.upper()))
    
    # Log configuration info
    root_logger.info("=" * 80)
    root_logger.info("Logging configured successfully")
    root_logger.info(f"Log file: {log_file_path}")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Console output: {console_output}")
    root_logger.info(f"Detailed format: {detailed_format}")
    root_logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_log_level(logger_name: str, level: str) -> None:
    """
    Set log level for a specific logger.
    
    Args:
        logger_name: Name of the logger
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))
    logging.info(f"Set log level for '{logger_name}' to {level}")


def configure_from_env() -> None:
    """
    Configure logging from environment variables.
    
    Environment variables:
        LOG_LEVEL: Default log level (default: INFO)
        LOG_FILE: Specific log file name (optional)
        LOG_DIR: Directory for log files (default: logs)
        LOG_CONSOLE: Enable console output (default: true)
        LOG_DETAILED: Use detailed format (default: false)
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")
    log_dir = os.getenv("LOG_DIR", "logs")
    console_output = os.getenv("LOG_CONSOLE", "true").lower() == "true"
    detailed_format = os.getenv("LOG_DETAILED", "false").lower() == "true"
    
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        log_dir=log_dir,
        console_output=console_output,
        detailed_format=detailed_format
    )


def configure_from_config(config) -> None:
    """
    Configure logging from AppConfig instance.
    
    Args:
        config: AppConfig instance from config.py
        
    Note:
        This is the preferred method when using the centralized config module.
    """
    setup_logging(
        log_level=config.logging.log_level,
        log_file=config.logging.log_file,
        log_dir=config.logging.log_dir,
        console_output=config.logging.log_console,
        detailed_format=config.logging.log_detailed
    )
    
    # Set component-specific log levels
    set_log_level("workflow", config.logging.workflow_log_level)
    set_log_level("nodes", config.logging.nodes_log_level)
    set_log_level("data_sources", config.logging.data_sources_log_level)


class ContextLogger:
    """
    Logger wrapper that adds context to log messages.
    
    Useful for adding session IDs, user IDs, or other contextual information
    to all log messages from a specific component.
    """
    
    def __init__(self, logger: logging.Logger, context: dict):
        """
        Initialize context logger.
        
        Args:
            logger: Base logger instance
            context: Dictionary of context to add to messages
        """
        self.logger = logger
        self.context = context
    
    def _format_message(self, message: str) -> str:
        """Format message with context."""
        context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
        return f"[{context_str}] {message}"
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with context."""
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with context."""
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message with context."""
        self.logger.critical(self._format_message(message), *args, **kwargs)


def create_context_logger(name: str, **context) -> ContextLogger:
    """
    Create a context logger with specified context.
    
    Args:
        name: Logger name
        **context: Context key-value pairs
        
    Returns:
        ContextLogger instance
        
    Example:
        >>> logger = create_context_logger("workflow", session_id="abc123")
        >>> logger.info("Processing query")
        # Output: [session_id=abc123] Processing query
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, context)


# Performance logging utilities

class PerformanceLogger:
    """
    Logger for tracking performance metrics.
    
    Useful for monitoring execution times and identifying bottlenecks.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize performance logger.
        
        Args:
            logger: Base logger instance
        """
        self.logger = logger
        self.timings = {}
    
    def start(self, operation: str) -> None:
        """
        Start timing an operation.
        
        Args:
            operation: Name of the operation
        """
        self.timings[operation] = datetime.now()
        self.logger.debug(f"Started: {operation}")
    
    def end(self, operation: str) -> float:
        """
        End timing an operation and log duration.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Duration in seconds
        """
        if operation not in self.timings:
            self.logger.warning(f"No start time found for operation: {operation}")
            return 0.0
        
        start_time = self.timings[operation]
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"Completed: {operation} (duration: {duration:.3f}s)")
        
        del self.timings[operation]
        return duration
    
    def log_metric(self, metric_name: str, value: float, unit: str = "") -> None:
        """
        Log a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Optional unit (e.g., 'ms', 'MB')
        """
        unit_str = f" {unit}" if unit else ""
        self.logger.info(f"Metric: {metric_name} = {value:.2f}{unit_str}")


def create_performance_logger(name: str) -> PerformanceLogger:
    """
    Create a performance logger.
    
    Args:
        name: Logger name
        
    Returns:
        PerformanceLogger instance
    """
    base_logger = logging.getLogger(name)
    return PerformanceLogger(base_logger)


if __name__ == "__main__":
    # Test logging configuration
    setup_logging(log_level="DEBUG", detailed_format=True)
    
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test context logger
    context_logger = create_context_logger("test", session_id="test123", user="testuser")
    context_logger.info("Testing context logger")
    
    # Test performance logger
    perf_logger = create_performance_logger("test.performance")
    perf_logger.start("test_operation")
    import time
    time.sleep(0.1)
    perf_logger.end("test_operation")
    perf_logger.log_metric("memory_usage", 150.5, "MB")
