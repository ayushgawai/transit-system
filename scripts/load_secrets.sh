#!/bin/bash
# Load secrets from secrets.yaml and export as environment variables
# Usage: source scripts/load_secrets.sh
#        or: source scripts/load_secrets.sh secrets.yaml

SECRETS_FILE="${1:-secrets.yaml}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS_PATH="${PROJECT_ROOT}/${SECRETS_FILE}"

if [ ! -f "$SECRETS_PATH" ]; then
    echo "Error: Secrets file not found at $SECRETS_PATH"
    echo "Please create secrets.yaml in the project root and fill in your credentials."
    echo "You can copy the template from secrets.yaml (if it exists) or create it manually."
    exit 1
fi

# Check if Python and PyYAML are available
if command -v python3 &> /dev/null; then
    # Use Python to parse YAML (more reliable than shell parsing)
    python3 << EOF
import yaml
import os
import sys

try:
    with open('$SECRETS_PATH', 'r') as f:
        secrets = yaml.safe_load(f) or {}
    
    # Flatten nested dictionaries (e.g., if someone uses nested structure)
    def flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    secrets = flatten_dict(secrets)
    
    # Export each key-value pair
    for key, value in secrets.items():
        # Skip empty values
        if value is None or value == "":
            continue
        # Convert value to string and escape special characters
        value_str = str(value).replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
        # Handle variable substitution (e.g., {AWS_ACCOUNT_ID})
        if '{AWS_ACCOUNT_ID}' in value_str:
            aws_account = secrets.get('AWS_ACCOUNT_ID', '')
            value_str = value_str.replace('{AWS_ACCOUNT_ID}', aws_account)
        # Print export statement
        print(f'export {key}="{value_str}"')
        
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error loading secrets: {e}", file=sys.stderr)
    sys.exit(1)
EOF

    # Capture Python output and eval it to export variables
    eval "$(python3 << EOF
import yaml
import os

with open('$SECRETS_PATH', 'r') as f:
    secrets = yaml.safe_load(f) or {}

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

secrets = flatten_dict(secrets)

for key, value in secrets.items():
    if value is None or value == "":
        continue
    value_str = str(value).replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
    if '{AWS_ACCOUNT_ID}' in value_str:
        aws_account = secrets.get('AWS_ACCOUNT_ID', '')
        value_str = value_str.replace('{AWS_ACCOUNT_ID}', aws_account)
    print(f'export {key}="{value_str}"')
EOF
)"
    
    echo "✓ Secrets loaded from $SECRETS_PATH"
    echo "✓ Environment variables exported"
else
    echo "Error: Python 3 not found. Please install Python 3 to use this script."
    exit 1
fi

