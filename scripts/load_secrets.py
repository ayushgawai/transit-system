#!/usr/bin/env python3
"""
Load secrets from secrets.yaml and export as environment variables.

This script reads secrets.yaml and exports all key-value pairs as environment variables.
It can be used standalone or sourced from shell scripts.

Usage:
    # Source from shell (recommended)
    source <(python scripts/load_secrets.py)
    
    # Or use the shell script wrapper
    source scripts/load_secrets.sh
    
    # Show what would be exported (without actually exporting)
    python scripts/load_secrets.py --show
"""

import os
import sys
import yaml
import argparse
from pathlib import Path


def load_secrets(secrets_path: str = "secrets.yaml") -> dict:
    """Load secrets from YAML file."""
    secrets_path = Path(secrets_path)
    
    if not secrets_path.exists():
        project_root = Path(__file__).parent.parent
        secrets_path = project_root / "secrets.yaml"
    
    if not secrets_path.exists():
        print(f"Error: Secrets file not found at {secrets_path}", file=sys.stderr)
        print("Please create secrets.yaml in the project root and fill in your credentials.", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(secrets_path, 'r') as f:
            secrets = yaml.safe_load(f) or {}
        return secrets
    except Exception as e:
        print(f"Error loading secrets: {e}", file=sys.stderr)
        sys.exit(1)


def flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def substitute_vars(value: str, secrets: dict) -> str:
    """Substitute {VAR_NAME} patterns in string using secrets dict."""
    import re
    
    def replace_var(match):
        var_name = match.group(1)
        return secrets.get(var_name, match.group(0))
    
    pattern = r'\{([^}]+)\}'
    return re.sub(pattern, replace_var, value)


def export_secrets(secrets: dict, show_only: bool = False):
    """Export secrets as environment variables."""
    # Flatten nested structure
    flattened = flatten_dict(secrets)
    
    # Substitute variables
    for key, value in flattened.items():
        if value is None or value == "":
            continue
        
        value_str = str(value)
        
        # Substitute {VAR_NAME} patterns
        if '{' in value_str:
            value_str = substitute_vars(value_str, flattened)
        
        if show_only:
            # Mask sensitive values
            if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'CREDENTIAL']):
                masked = "*" * min(len(value_str), 20) + "..." if len(value_str) > 20 else "*" * len(value_str)
                print(f"{key}={masked}")
            else:
                print(f"{key}={value_str}")
        else:
            # Export to environment
            os.environ[key] = value_str
            # Print export statement for shell sourcing
            value_escaped = value_str.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
            print(f'export {key}="{value_escaped}"')


def main():
    parser = argparse.ArgumentParser(description="Load secrets from secrets.yaml and export as environment variables")
    parser.add_argument("--secrets-file", default="secrets.yaml", help="Path to secrets.yaml file")
    parser.add_argument("--show", action="store_true", help="Show secrets without exporting (masks sensitive values)")
    parser.add_argument("--no-mask", action="store_true", help="Don't mask sensitive values when showing")
    
    args = parser.parse_args()
    
    # Load secrets
    secrets = load_secrets(args.secrets_file)
    
    if args.show:
        # Show mode
        flattened = flatten_dict(secrets)
        for key, value in sorted(flattened.items()):
            if value is None or value == "":
                continue
            
            value_str = str(value)
            if '{' in value_str:
                value_str = substitute_vars(value_str, flattened)
            
            if not args.no_mask and any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'CREDENTIAL']):
                masked = "*" * min(len(value_str), 20) + "..." if len(value_str) > 20 else "*" * len(value_str)
                print(f"{key}={masked}")
            else:
                print(f"{key}={value_str}")
    else:
        # Export mode
        export_secrets(secrets, show_only=False)


if __name__ == "__main__":
    main()

