"""
Configuration loader - Loads and merges multiple YAML config files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Supported config versions
SUPPORTED_CONFIG_VERSIONS = ["1.0.0"]


def _load_single_config(config_path: Path) -> Dict[str, Any]:
    """
    Load a single YAML config file.
    
    Args:
        config_path: Path to config YAML file
        
    Returns:
        Dictionary containing configuration
    """
    with open(config_path, 'r', encoding='utf-8') as yaml_file_handle:
        config = yaml.safe_load(yaml_file_handle)
    
    if not config:
        raise ValueError(f"Config file is empty: {config_path}")
    
    # Validate version is supported
    config_version = config.get("config_version")
    if config_version and config_version not in SUPPORTED_CONFIG_VERSIONS:
        raise ValueError(
            f"Unsupported config version: {config_version}. "
            f"Supported versions: {SUPPORTED_CONFIG_VERSIONS}"
        )
    
    return config


def _merge_configs(configs: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple config dictionaries, later configs override earlier ones.
    
    Args:
        configs: List of config dictionaries to merge
        
    Returns:
        Merged configuration dictionary
    """
    merged_config = {}
    for config in configs:
        merged_config.update(config)
    return merged_config


def load_config(config_dir: str) -> Dict[str, Any]:
    """
    Load and merge all YAML config files from a directory.
    
    Config files are loaded in alphabetical order and merged. Later files override
    earlier ones for duplicate keys. Expected config files:
    - servicenow.yaml: ServiceNow API configuration
    - app.yaml: Application settings
    - logging.yaml: Logging configuration
    
    Args:
        config_dir: Path to config directory (e.g., "configs/dev")
        
    Returns:
        Dictionary containing merged configuration
        
    Raises:
        FileNotFoundError: If config directory doesn't exist
    """
    config_directory = Path(config_dir)
    
    if not config_directory.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")
    
    # Load all YAML files in the directory
    config_files = sorted(config_directory.glob("*.yaml"))
    
    if not config_files:
        raise ValueError(f"No config files found in: {config_dir}")
    
    configs = []
    for config_file in config_files:
        config = _load_single_config(config_file)
        configs.append(config)
    
    # Merge all configs
    merged_config = _merge_configs(configs)
    
    # Load ServiceNow URL from environment variable
    if "servicenow" in merged_config:
        instance_url = os.getenv("SERVICENOW_INSTANCE_URL", "")
        if instance_url:
            merged_config["servicenow"]["instance_url"] = instance_url
    
    return merged_config
