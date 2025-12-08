#!/bin/bash
# Run DBT commands with proper environment setup
# Usage: ./scripts/run_dbt.sh [dbt-command] [args...]
#        The script will auto-detect target from config.yaml or profiles.yml
#        Or specify: ./scripts/run_dbt.sh debug --target snowflake

cd "$(dirname "$0")/.."

# Activate venv
source venv/bin/activate

# Extract target from dbt args if provided (e.g., --target snowflake)
TARGET=""
ARGS=("$@")
for i in "${!ARGS[@]}"; do
    if [ "${ARGS[$i]}" = "--target" ] && [ -n "${ARGS[$((i+1))]}" ]; then
        TARGET="${ARGS[$((i+1))]}"
        break
    fi
done

# Set DBT environment variables (auto-detect or use provided target)
if [ -n "$TARGET" ]; then
    source scripts/set_dbt_env.sh "$TARGET"
else
    source scripts/set_dbt_env.sh
fi

# Change to dbt directory
cd dbt/transit_dbt

# Run dbt command with all arguments
dbt "$@"

