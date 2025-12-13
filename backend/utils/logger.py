"""
Logging utility - Configures and provides logging functionality.

Reads logging configuration from YAML config file and sets up file and console handlers.
"""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(config: dict, logger_name: str = "sr_automation") -> logging.Logger:
    """Set up logger based on configuration from YAML config file."""
    # Get logging config from config dictionary
    sr_logging_config = config.get("logging", {})
    
    # Get log level (default to INFO if not specified)
    sr_log_level_str = sr_logging_config.get("level", "INFO").upper()
    sr_log_level = getattr(logging, sr_log_level_str, logging.INFO)
    
    # Get log format (default format if not specified)
    sr_log_format = sr_logging_config.get(
        "format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Get log file path (default to logs/app.log)
    sr_log_file_path = sr_logging_config.get("file", "logs/app.log")
    
    # Create logger instance
    logger = logging.getLogger(logger_name)
    logger.setLevel(sr_log_level)
    
    # Avoid adding handlers multiple times if logger already configured
    if logger.handlers:
        return logger
    
    # Create formatter
    sr_log_formatter = logging.Formatter(sr_log_format)
    
    # Set up file handler with rotation
    # Rotate when file reaches 10MB, keep 5 backup files
    log_file_path = Path(sr_log_file_path)
    
    # Create log directory if it doesn't exist
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation (max 10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(sr_log_level)
    file_handler.setFormatter(sr_log_formatter)
    logger.addHandler(file_handler)
    
    # Set up console handler (for development/debugging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(sr_log_level)
    console_handler.setFormatter(sr_log_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(logger_name: str = "sr_automation") -> logging.Logger:
    """Get an existing logger instance by name."""
    return logging.getLogger(logger_name)

