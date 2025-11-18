#!/bin/bash
# Load environment variables from .env file
# Usage: source scripts/load_env.sh

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    echo "Please copy .env.example to .env and fill in your values"
    exit 1
fi

# Export all variables from .env file
# This handles variables that reference other variables (e.g., ${AWS_ACCOUNT_ID})
set -a
source "$ENV_FILE"
set +a

echo "✓ Environment variables loaded from $ENV_FILE"

