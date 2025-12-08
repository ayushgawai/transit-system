#!/bin/bash
# Set DBT environment variables from AWS Secrets Manager
# Supports both Redshift and Snowflake based on target or config
# Usage: source scripts/set_dbt_env.sh [redshift|snowflake]
#        If no argument, reads from config.yaml or profiles.yml

export AWS_PROFILE=transit-system
export AWS_REGION=us-west-2

# Determine target (from argument, config.yaml, or profiles.yml)
TARGET="${1:-}"

if [ -z "$TARGET" ]; then
    # Try to read from config.yaml
    if [ -f "config.yaml" ]; then
        TARGET=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')).get('warehouse', {}).get('type', 'redshift'))" 2>/dev/null || echo "redshift")
    fi
    
    # If still empty, try profiles.yml
    if [ -z "$TARGET" ] && [ -f "dbt/transit_dbt/profiles.yml" ]; then
        TARGET=$(grep -A 1 "^  target:" dbt/transit_dbt/profiles.yml | tail -1 | sed 's/.*: *//' | tr -d ' ')
    fi
    
    # Default to snowflake if still empty
    TARGET="${TARGET:-snowflake}"
fi

echo "🔧 Setting DBT environment variables for: $TARGET"
echo ""

if [ "$TARGET" = "snowflake" ]; then
    # Get Snowflake credentials from Secrets Manager
    SNOWFLAKE_SECRET=$(aws secretsmanager get-secret-value \
      --secret-id transit/snowflake-dev \
      --profile transit-system \
      --region us-west-2 \
      --query SecretString \
      --output text)
    
    # Parse and export Snowflake variables
    export SNOWFLAKE_ACCOUNT=$(echo $SNOWFLAKE_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['account'])")
    export SNOWFLAKE_USER=$(echo $SNOWFLAKE_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['user'])")
    export SNOWFLAKE_PASSWORD=$(echo $SNOWFLAKE_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['password'])")
    export SNOWFLAKE_WAREHOUSE=$(echo $SNOWFLAKE_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin).get('warehouse', 'HORNET_QUERY_WH'))")
    export SNOWFLAKE_DATABASE=$(echo $SNOWFLAKE_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin).get('database', 'USER_DB_HORNET'))")
    export SNOWFLAKE_ROLE=$(echo $SNOWFLAKE_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin).get('role', 'TRAINING_ROLE'))")
    export SNOWFLAKE_SCHEMA=ANALYTICS
    
    echo "✅ Snowflake environment variables set"
    echo "   Account: ${SNOWFLAKE_ACCOUNT:0:30}..."
    echo "   User: $SNOWFLAKE_USER"
    echo "   Database: $SNOWFLAKE_DATABASE"
    echo "   Warehouse: $SNOWFLAKE_WAREHOUSE"
    
elif [ "$TARGET" = "redshift" ]; then
    # Get Redshift credentials from Secrets Manager
    REDSHIFT_SECRET=$(aws secretsmanager get-secret-value \
      --secret-id transit/redshift-dev \
      --profile transit-system \
      --region us-west-2 \
      --query SecretString \
      --output text)
    
    # Parse and export Redshift variables
    export REDSHIFT_HOST=$(echo $REDSHIFT_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['host'])")
    export REDSHIFT_PORT=$(echo $REDSHIFT_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['port'])")
    export REDSHIFT_USER=$(echo $REDSHIFT_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['user'])")
    export REDSHIFT_PASSWORD=$(echo $REDSHIFT_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['password'])")
    export REDSHIFT_DATABASE=$(echo $REDSHIFT_SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['database'])")
    export REDSHIFT_SCHEMA=public
    
    echo "✅ Redshift environment variables set"
    echo "   Host: ${REDSHIFT_HOST:0:50}..."
    echo "   Database: $REDSHIFT_DATABASE"
else
    echo "❌ Unknown target: $TARGET (use 'redshift' or 'snowflake')"
    return 1
fi

