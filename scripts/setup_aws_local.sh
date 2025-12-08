#!/bin/bash
# Setup AWS services for local testing
# Creates S3 bucket, uploads scripts, sets up Secrets Manager

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
REGION="us-west-2"
PROFILE="transit-system"
ACCOUNT_ID="436204347796"

# S3 Bucket names
SCRIPTS_BUCKET="transit-scripts-${ACCOUNT_ID}-dev"
DATA_BUCKET="transit-data-${ACCOUNT_ID}-dev"

echo "🚀 Setting up AWS services for local testing..."
echo ""

# 1. Create S3 buckets
echo "📦 Creating S3 buckets..."
aws s3 mb s3://${SCRIPTS_BUCKET} --region ${REGION} --profile ${PROFILE} 2>/dev/null || echo "Bucket ${SCRIPTS_BUCKET} already exists"
aws s3 mb s3://${DATA_BUCKET} --region ${REGION} --profile ${PROFILE} 2>/dev/null || echo "Bucket ${DATA_BUCKET} already exists"

# 2. Upload scripts to S3
echo "📤 Uploading scripts to S3..."
aws s3 sync "${PROJECT_ROOT}/ingestion/" \
  "s3://${SCRIPTS_BUCKET}/scripts/ingestion/" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude "*.log" \
  --region ${REGION} \
  --profile ${PROFILE}

# Upload dbt project
aws s3 sync "${PROJECT_ROOT}/dbt/" \
  "s3://${SCRIPTS_BUCKET}/scripts/dbt/" \
  --exclude "target/*" \
  --exclude "logs/*" \
  --exclude "*.log" \
  --region ${REGION} \
  --profile ${PROFILE}

echo "✅ Scripts uploaded to S3"

# 3. Set up Secrets Manager
echo "🔐 Setting up Secrets Manager..."

# Load Snowflake credentials from secrets.yaml
SNOWFLAKE_ACCOUNT=$(grep "SNOWFLAKE_ACCOUNT:" "${PROJECT_ROOT}/secrets.yaml" | cut -d'"' -f2)
SNOWFLAKE_USER=$(grep "SNOWFLAKE_USER:" "${PROJECT_ROOT}/secrets.yaml" | cut -d'"' -f2)
SNOWFLAKE_PASSWORD=$(grep "SNOWFLAKE_PASSWORD:" "${PROJECT_ROOT}/secrets.yaml" | cut -d'"' -f2)
SNOWFLAKE_WAREHOUSE=$(grep "SNOWFLAKE_WAREHOUSE:" "${PROJECT_ROOT}/secrets.yaml" | cut -d'"' -f2)
SNOWFLAKE_DATABASE=$(grep "SNOWFLAKE_DATABASE:" "${PROJECT_ROOT}/secrets.yaml" | cut -d'"' -f2)

# Create Snowflake secret
SECRET_JSON=$(cat <<EOF
{
  "account": "${SNOWFLAKE_ACCOUNT}",
  "user": "${SNOWFLAKE_USER}",
  "password": "${SNOWFLAKE_PASSWORD}",
  "warehouse": "${SNOWFLAKE_WAREHOUSE}",
  "database": "${SNOWFLAKE_DATABASE}",
  "role": "TRAINING_ROLE"
}
EOF
)

aws secretsmanager create-secret \
  --name transit/snowflake-dev \
  --description "Snowflake credentials for transit system" \
  --secret-string "${SECRET_JSON}" \
  --region ${REGION} \
  --profile ${PROFILE} \
  2>/dev/null || aws secretsmanager update-secret \
    --secret-id transit/snowflake-dev \
    --secret-string "${SECRET_JSON}" \
    --region ${REGION} \
    --profile ${PROFILE}

echo "✅ Secrets Manager configured"

# 4. Set environment variables for Airflow
echo ""
echo "📝 Set these environment variables for Airflow:"
echo "export TRANSIT_S3_BUCKET=${SCRIPTS_BUCKET}"
echo "export AWS_PROFILE=${PROFILE}"
echo "export AWS_REGION=${REGION}"
echo ""
echo "✅ AWS setup complete!"

