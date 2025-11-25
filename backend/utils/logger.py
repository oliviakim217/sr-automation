"""
Logging utility - Configures and provides logging functionality.

Reads logging configuration from YAML config file and sets up file and console handlers.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logger(config: dict, logger_name: str = "sr_automation") -> logging.Logger:
    """
    Set up logger based on configuration from YAML config file.
    
    Configures both file and console handlers with rotation support.
    Creates log directory if it doesn't exist.
    
    Args:
        config: Dictionary containing logging configuration (from config file)
        logger_name: Name for the logger instance (default: "sr_automation")
        
    Returns:
        Configured logger instance
        
    Example:
        from backend.config import load_config
        from backend.utils.logger import setup_logger
        
        config = load_config("configs/dev/config.yaml")
        logger = setup_logger(config.get("logging", {}))
        logger.info("Application started")
    """
    # Get logging config from config dictionary
    logging_config = config.get("logging", {})
    
    # Get log level (default to INFO if not specified)
    log_level_str = logging_config.get("level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Get log format (default format if not specified)
    log_format = logging_config.get(
        "format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Get log file path (default to logs/app.log)
    log_file = logging_config.get("file", "logs/app.log")
    
    # Create logger instance
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times if logger already configured
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Set up file handler with rotation
    # Rotate when file reaches 10MB, keep 5 backup files
    log_file_path = Path(log_file)
    
    # Create log directory if it doesn't exist
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation (max 10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Set up console handler (for development/debugging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(logger_name: str = "sr_automation") -> logging.Logger:
    """
    Get an existing logger instance by name.
    
    Useful when you already have a configured logger and just need to retrieve it.
    
    Args:
        logger_name: Name of the logger to retrieve
        
    Returns:
        Logger instance (may be unconfigured if setup_logger hasn't been called)
    """
    return logging.getLogger(logger_name)

