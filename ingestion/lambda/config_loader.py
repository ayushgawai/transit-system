"""
Utility module for loading configuration from YAML file.

This module provides functions to load and parse the master config file,
with support for environment variable substitution.
"""

import os
import yaml
from typing import Dict, Any, Optional


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable substitution.
    
    Args:
        config_path: Path to config YAML file
        
    Returns:
        Configuration dictionary with environment variables resolved
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if config is None:
        config = {}
    
    # Recursively replace environment variable placeholders
    config = _replace_env_vars(config)
    
    return config


def _replace_env_vars(obj: Any) -> Any:
    """
    Recursively replace environment variable placeholders in config.
    
    Handles placeholders like "${VAR_NAME}" or "${VAR_NAME:-default_value}".
    
    Args:
        obj: Config object (dict, list, or string)
        
    Returns:
        Object with environment variables replaced
    """
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        # Check if string contains environment variable placeholder
        if obj.startswith("${") and obj.endswith("}"):
            var_expr = obj[2:-1]  # Remove ${ and }
            
            # Check for default value syntax: ${VAR:-default}
            if ":-" in var_expr:
                var_name, default_value = var_expr.split(":-", 1)
                return os.environ.get(var_name, default_value)
            else:
                # No default value, return None if not set
                return os.environ.get(var_expr, obj)
        return obj
    else:
        return obj


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a config value using dot-notation path.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path (e.g., "transit_app.api_key")
        default: Default value if key not found
        
    Returns:
        Config value or default
    """
    keys = key_path.split(".")
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def get_aws_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get AWS configuration section."""
    return config.get("aws", {})


def get_snowflake_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get Snowflake configuration section."""
    return config.get("snowflake", {})


def get_transit_app_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get TransitApp configuration section."""
    return config.get("transit_app", {})


def get_chatbot_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get chatbot configuration section."""
    return config.get("chatbot", {})

