#!/bin/bash
# Start the Transit Ops API Server

cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Load secrets
export $(python3 -c "
import yaml
with open('secrets.yaml', 'r') as f:
    secrets = yaml.safe_load(f)
for k, v in secrets.items():
    if v:
        print(f'{k}={v}')
" | xargs)

# Start API
cd api
echo "Starting API server on http://localhost:8000..."
python main.py

