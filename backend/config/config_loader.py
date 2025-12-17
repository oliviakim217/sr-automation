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
    """Load a single YAML config file."""
    with open(config_path, 'r', encoding='utf-8') as yaml_file_handle:
        cfg_loaded = yaml.safe_load(yaml_file_handle)
    
    if not cfg_loaded:
        raise ValueError(f"Config file is empty: {config_path}")
    
    # Validate version is supported
    config_version = cfg_loaded.get("config_version")
    if config_version and config_version not in SUPPORTED_CONFIG_VERSIONS:
        raise ValueError(
            f"Unsupported config version: {config_version}. "
            f"Supported versions: {SUPPORTED_CONFIG_VERSIONS}"
        )
    
    return cfg_loaded


def _merge_configs(cfg_list: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple config dictionaries, later configs override earlier ones."""
    cfg_merged = {}
    for cfg_item in cfg_list:
        cfg_merged.update(cfg_item)
    return cfg_merged


def load_config(config_dir: str) -> Dict[str, Any]:
    """Load and merge all YAML config files from a directory."""
    config_directory = Path(config_dir)
    
    if not config_directory.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")
    
    # Load all YAML files in the directory
    config_files = sorted(config_directory.glob("*.yaml"))
    
    if not config_files:
        raise ValueError(f"No config files found in: {config_dir}")
    
    cfg_list = []
    for config_file in config_files:
        cfg_loaded = _load_single_config(config_file)
        cfg_list.append(cfg_loaded)
    
    # Merge all configs
    cfg_merged = _merge_configs(cfg_list)
    
    # Load ServiceNow URL from environment variable
    if "servicenow" in cfg_merged:
        instance_url = os.getenv("SERVICENOW_INSTANCE_URL", "")
        if instance_url:
            cfg_merged["servicenow"]["instance_url"] = instance_url
    
    return cfg_merged
