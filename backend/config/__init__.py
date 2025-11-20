"""
Config package - Configuration management.

Handles loading and managing configuration files with version validation.
"""

from .config_loader import load_config, SUPPORTED_CONFIG_VERSIONS

__all__ = ["load_config", "SUPPORTED_CONFIG_VERSIONS"]

