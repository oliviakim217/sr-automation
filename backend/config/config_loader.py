"""
Configuration loader - Simple YAML config loader with version validation.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Supported config versions
SUPPORTED_CONFIG_VERSIONS = ["1.0.0"]


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Expected config structure:
    - config_version: Version string (e.g., "1.0.0")
    - servicenow: ServiceNow API configuration
      - instance_url: ServiceNow instance URL (loaded from env var)
      - api_path: API base path (e.g., "/api/now/table")
      - query_params: Default query parameters
      - headers: HTTP headers for API requests
    - app: Application settings (name, version, environment)
    - logging: Logging configuration (level, format, file)
    
    Args:
        config_path: Path to config YAML file (e.g., "configs/dev/config.yaml")
        
    Returns:
        Dictionary containing configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config version is unsupported
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Load YAML config
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    if not config:
        raise ValueError(f"Config file is empty: {config_path}")
    
    # Validate version is supported
    config_version = config.get("config_version")
    if config_version and config_version not in SUPPORTED_CONFIG_VERSIONS:
        raise ValueError(
            f"Unsupported config version: {config_version}. "
            f"Supported versions: {SUPPORTED_CONFIG_VERSIONS}"
        )
    
    # Load ServiceNow URL from environment variable
    if "servicenow" in config:
        instance_url = os.getenv("SERVICENOW_INSTANCE_URL", "")
        if instance_url:
            config["servicenow"]["instance_url"] = instance_url
    
    return config
