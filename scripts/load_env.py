#!/usr/bin/env python3
"""
Load and export environment variables from .env file.

This script can be used to:
1. Load .env file and export to current shell
2. Export to AWS Secrets Manager
3. Export to Airflow variables
4. Update config files

Usage:
    python scripts/load_env.py --export-shell    # Export to current shell
    python scripts/load_env.py --export-aws      # Export to AWS Secrets Manager
    python scripts/load_env.py --show            # Show loaded variables (without secrets)
"""

import os
import sys
import argparse
import boto3
from pathlib import Path
from typing import Dict, Any

# Sensitive keys to mask when displaying
SENSITIVE_KEYS = ['password', 'key', 'secret', 'token', 'credential']


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """
    Load environment variables from .env file.
    
    Supports variable substitution like ${VAR_NAME} or ${VAR_NAME:-default}
    """
    env_path = Path(env_path)
    
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at {env_path}. Copy .env.example to .env and configure it.")
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                env_vars[key] = value
    
    # Substitute variables (e.g., ${VAR_NAME} or ${VAR_NAME:-default})
    for key, value in env_vars.items():
        env_vars[key] = substitute_vars(value, env_vars)
    
    return env_vars


def substitute_vars(value: str, env_vars: Dict[str, str]) -> str:
    """Substitute ${VAR_NAME} or ${VAR_NAME:-default} patterns in string."""
    import re
    
    def replace_var(match):
        var_expr = match.group(1)
        if ':-' in var_expr:
            var_name, default_value = var_expr.split(':-', 1)
            return env_vars.get(var_name, default_value)
        else:
            return env_vars.get(var_expr, match.group(0))
    
    pattern = r'\$\{([^}]+)\}'
    return re.sub(pattern, replace_var, value)


def export_to_shell(env_vars: Dict[str, str]):
    """Print export statements for shell."""
    for key, value in env_vars.items():
        # Escape special characters in value
        value_escaped = value.replace('"', '\\"').replace('$', '\\$')
        print(f'export {key}="{value_escaped}"')


def export_to_aws_secrets_manager(env_vars: Dict[str, str], secret_name: str = "transit/system/env"):
    """Export environment variables to AWS Secrets Manager."""
    try:
        secrets_client = boto3.client('secretsmanager')
        
        # Convert to JSON string
        import json
        secret_string = json.dumps(env_vars, indent=2)
        
        try:
            # Try to update existing secret
            secrets_client.update_secret(
                SecretId=secret_name,
                SecretString=secret_string
            )
            print(f"✓ Updated secret: {secret_name}")
        except secrets_client.exceptions.ResourceNotFoundException:
            # Create new secret
            secrets_client.create_secret(
                Name=secret_name,
                SecretString=secret_string,
                Description="Transit System Environment Variables"
            )
            print(f"✓ Created secret: {secret_name}")
            
    except Exception as e:
        print(f"✗ Error exporting to AWS Secrets Manager: {str(e)}")
        sys.exit(1)


def show_vars(env_vars: Dict[str, str], mask_sensitive: bool = True):
    """Display environment variables (masking sensitive ones)."""
    print("\n" + "="*60)
    print("Environment Variables")
    print("="*60)
    
    for key, value in sorted(env_vars.items()):
        if mask_sensitive and any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            masked_value = "*" * min(len(value), 20) + "..." if len(value) > 20 else "*" * len(value)
            print(f"{key}={masked_value}")
        else:
            print(f"{key}={value}")
    
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Load and export environment variables from .env file")
    parser.add_argument("--env-file", default=".env", help="Path to .env file")
    parser.add_argument("--export-shell", action="store_true", help="Export to shell (print export statements)")
    parser.add_argument("--export-aws", action="store_true", help="Export to AWS Secrets Manager")
    parser.add_argument("--secret-name", default="transit/system/env", help="AWS Secrets Manager secret name")
    parser.add_argument("--show", action="store_true", help="Show loaded variables")
    parser.add_argument("--no-mask", action="store_true", help="Don't mask sensitive values")
    
    args = parser.parse_args()
    
    try:
        # Load environment variables
        env_vars = load_env_file(args.env_file)
        
        if args.export_shell:
            export_to_shell(env_vars)
        elif args.export_aws:
            export_to_aws_secrets_manager(env_vars, args.secret_name)
        elif args.show:
            show_vars(env_vars, mask_sensitive=not args.no_mask)
        else:
            # Default: just load into current environment
            for key, value in env_vars.items():
                os.environ[key] = value
            print(f"✓ Loaded {len(env_vars)} environment variables from {args.env_file}")
            print("Note: Variables are loaded into current Python process only.")
            print("For shell export, use: source <(python scripts/load_env.py --export-shell)")
            
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

