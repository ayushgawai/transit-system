# Scripts Directory

Utility scripts for the Transit System project.

## load_env.sh

Bash script to load environment variables from `.env` file.

**Usage:**
```bash
source scripts/load_env.sh
# or
source scripts/load_env.sh .env  # Specify custom .env file
```

This script exports all variables from `.env` to the current shell session.

## load_env.py

Python script to load and manage environment variables from `.env` file.

**Usage:**

```bash
# Load variables into current Python process
python scripts/load_env.py

# Export to shell (print export statements)
python scripts/load_env.py --export-shell | source /dev/stdin

# Export to AWS Secrets Manager
python scripts/load_env.py --export-aws --secret-name transit/system/env

# Show loaded variables (masking sensitive ones)
python scripts/load_env.py --show

# Show all variables (including sensitive ones)
python scripts/load_env.py --show --no-mask

# Use custom .env file
python scripts/load_env.py --env-file .env.prod
```

**Features:**
- Loads environment variables from `.env` file
- Supports variable substitution (e.g., `${VAR_NAME}` or `${VAR_NAME:-default}`)
- Can export to AWS Secrets Manager for deployment
- Masks sensitive values when displaying
- Works with both local development and deployment

## Setting Up Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your values

3. Load variables:
```bash
source scripts/load_env.sh
```

All scripts, dbt, Airflow, and deployment tools will automatically use these environment variables.

