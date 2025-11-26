# Transit System - Setup & Local Testing Guide

This guide walks you through setting up and testing the Transit Service Reliability & Demand Planning System locally **before deploying to AWS**. Follow these steps in order.

## 📋 Prerequisites

1. **Python 3.9+** installed
2. **dbt** installed (you mentioned: `/Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate`)
3. **Docker** installed (for local Airflow)
4. **AWS CLI** installed and configured (for local testing with S3)
5. **Snowflake Account** (free trial: $400 credits for 30 days)
6. **TransitApp API Key** (request at https://transit.land/api)

## 🔧 Step 1: Clone and Setup Python Environment

```bash
cd /Users/spartan/Documents/MSDA/Project/transit-system

# Create virtual environment (if not already created)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🔑 Step 2: Configure Secrets and Environment Variables

**Option A: Using secrets.yaml (Recommended - One file for everything)**

1. **Edit `secrets.yaml` and fill in all your credentials:**
```bash
# Open secrets.yaml in your editor
nano secrets.yaml  # or use your preferred editor (VS Code, vim, etc.)
```

Fill in at minimum:
- `SNOWFLAKE_ACCOUNT`: Your Snowflake account (e.g., `xy12345.us-west-2`)
- `SNOWFLAKE_USER`: Your Snowflake username
- `SNOWFLAKE_PASSWORD`: Your Snowflake password
- `SNOWFLAKE_WAREHOUSE`: `TRANSIT_WH` (or your warehouse name)
- `SNOWFLAKE_DATABASE`: `TRANSIT_DB` (or your database name)
- `SNOWFLAKE_ROLE`: `TRANSIT_ROLE` (or your role name)
- `TRANSIT_APP_API_KEY`: Your TransitApp API key (get from https://transit.land/api)
- `OPENAI_API_KEY`: Your OpenAI API key (optional, for chatbot)
- `AWS_REGION`: Your AWS region (e.g., `us-west-2`)
- `AWS_PROFILE`: AWS CLI profile name (e.g., `transit-system`)
- `AWS_ACCOUNT_ID`: Your AWS account ID

2. **Load secrets into environment variables:**
```bash
# Load all secrets from secrets.yaml
source scripts/load_secrets.sh
```

**Option B: Using .env file (Alternative)**

1. **Copy the .env example file:**
```bash
cp .env.example .env
```

2. **Edit `.env` and fill in your values**

3. **Load environment variables:**
```bash
source scripts/load_env.sh
```

**Verify environment variables are loaded:**
```bash
echo $SNOWFLAKE_ACCOUNT
echo $SNOWFLAKE_USER
```

**Important:** 
- Never commit `secrets.yaml` or `.env` files (already in `.gitignore`)
- Use `secrets.yaml` for convenience (one file for all credentials)
- All scripts, dbt, Airflow will automatically use these environment variables
- See [SECRETS.md](./SECRETS.md) for more details on secrets management

## 🪣 Step 3: Setup AWS Profile (for Local Testing)

Configure AWS CLI with your credentials:

```bash
aws configure --profile transit-system

# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-west-2)
# - Default output format (json)
```

**Set AWS_PROFILE in .env:**
```bash
# Edit .env and set:
AWS_PROFILE=transit-system
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=your_account_id  # Get from: aws sts get-caller-identity --query Account --output text
```

**Verify AWS access:**
```bash
aws s3 ls --profile transit-system
```

## ❄️ Step 4: Setup Snowflake

1. **Log into Snowflake** (https://app.snowflake.com)

2. **Create Database and Schemas:**
```bash
cd snowflake/setup

# Option A: Using snowsql CLI
snowsql -a YOUR_ACCOUNT.us-west-2 -u YOUR_USERNAME -f schema.sql

# Option B: Copy and paste schema.sql into Snowflake worksheet
```

3. **Run permissions script:**
```bash
snowsql -a YOUR_ACCOUNT.us-west-2 -u YOUR_USERNAME -f permissions.sql
```

4. **Verify setup:**
```sql
-- Run in Snowflake worksheet
USE DATABASE TRANSIT_DB;
SHOW SCHEMAS;
USE SCHEMA RAW;
SHOW TABLES;
```

## 📦 Step 5: Setup dbt Project

1. **Activate your dbt environment:**
```bash
source /Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate
```

2. **Navigate to dbt project:**
```bash
cd dbt/transit_dbt
```

3. **dbt profiles are already configured!**

The `dbt/transit_dbt/profiles.yml` file uses environment variables from your `.env` file. Just make sure:
- Your `.env` file is configured (Step 2)
- Environment variables are loaded (`source scripts/load_env.sh`)

**dbt uses this schema structure:**
- `RAW`: Raw data from Snowpipe
- `STAGING`: Cleaned data (views)
- `TRANSFORM`: Intermediate transformations (tables)
- `ANALYTICS`: Analytics marts (tables)
- `ML`: ML models and forecasts (tables)

4. **Test dbt connection:**
```bash
dbt debug --profiles-dir ~/.dbt
```

5. **Install dbt dependencies:**
```bash
dbt deps
```

6. **Test dbt models (after data is loaded):**
```bash
# Run staging models (views)
dbt run --select staging.*
dbt test --select staging.*

# Run transform models (if you have any)
dbt run --select transform.*

# Run analytics models
dbt run --select analytics.*
dbt test --select analytics.*
```

## 🧪 Step 6: Local Testing - Data Ingestion

Test ingestion locally before deploying to Lambda:

1. **Make sure .env is loaded:**
```bash
# Load environment variables from .env
source scripts/load_env.sh

# Or if you prefer manual export:
export USE_S3=false  # Set to true if you want to upload to S3
```

2. **Run local ingestion test:**
```bash
cd ingestion
python test_ingestion_local.py
```

This script will:
- Load config from `config/config.yaml`
- Call TransitApp API (respects rate limits: 5 calls/min)
- Save data to `data/local_test/` (or upload to S3 if configured)
- Test GTFS sync

**Note:** If you don't have AWS credentials configured, the script will save data locally. This is fine for local testing!

3. **Verify data:**
```bash
# Check local files
ls -la data/local_test/transitapp/

# Or if using S3:
aws s3 ls s3://YOUR-RAW-BUCKET/transitapp/ --profile transit-system --recursive
```

## 🔄 Step 7: Setup Local Airflow (Optional)

For local testing and development:

1. **Set Airflow environment variable:**
```bash
export AIRFLOW_UID=$(id -u)
export AIRFLOW_PROJ_DIR=/Users/spartan/Documents/MSDA/Project/transit-system/airflow
```

2. **Copy DAGs to your Airflow DAGs folder:**
```bash
# You mentioned DAGs are at: /Users/spartan/airflow-clean/dags/
cp airflow/dags/*.py /Users/spartan/airflow-clean/dags/
```

3. **Update Airflow DAGs with correct paths:**
   - Edit DAGs to use your local dbt path: `/Users/spartan/Documents/MSDA/Project/transit-system/dbt/transit_dbt`
   - Update Airflow variables/connections in Airflow UI:
     - AWS connection: `aws_default` (use AWS profile)
     - Snowflake connection: `snowflake_default`
     - Variables:
       - `dbt_project_dir`: `/Users/spartan/Documents/MSDA/Project/transit-system/dbt/transit_dbt`
       - `dbt_profiles_dir`: `~/.dbt`
       - `dbt_target`: `dev`
       - `transit_api_ingestion_function_name`: `transit-api-ingestion-dev`
       - `transit_gtfs_sync_function_name`: `transit-gtfs-sync-dev`

4. **Start Airflow (if using Docker):**
```bash
cd airflow
docker-compose up -d
```

5. **Access Airflow UI:**
   - URL: http://localhost:8080
   - Username: `airflow` (default)
   - Password: `airflow` (default)

## 🤖 Step 8: Test Chatbot Locally

1. **Make sure .env is loaded:**
```bash
source scripts/load_env.sh
```

2. **Run chatbot API:**
```bash
cd chatbot
python chatbot_api.py
```

3. **Test chatbot API:**
```bash
# In another terminal
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which route tomorrow at 8am is likely to be most crowded?"}'
```

## 📊 Step 9: Test Dashboard Queries

1. **Log into Snowflake**
2. **Navigate to Snowsight** (Worksheets)
3. **Test queries from dashboard/snowsight_queries/:**
```bash
cd dashboard/snowsight_queries

# Copy and paste SQL queries into Snowflake worksheet
# Test each query:
# - reliability_dashboard.sql
# - demand_crowding_dashboard.sql
# - forecasting_dashboard.sql
# - revenue_dashboard.sql
# - decision_support_dashboard.sql
```

## 🔍 Step 10: Verify End-to-End Data Flow

Test the complete pipeline locally:

1. **Run local ingestion:**
```bash
cd ingestion
python test_ingestion_local.py
```

2. **Manually load data into Snowflake** (if not using Snowpipe):
   - Upload test JSON files to S3
   - Use Snowflake UI to load from S3 stage
   - Or use `COPY INTO` commands

3. **Run dbt transformations:**
```bash
cd dbt/transit_dbt
source /Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate

# Load environment variables
source ../../scripts/load_env.sh

# Run transformations in order
dbt run --select staging.*
dbt run --select transform.*  # If you have transform models
dbt run --select analytics.*
```

4. **Verify data in Snowflake:**
```sql
-- Check raw data
SELECT COUNT(*) FROM RAW.TRANSITAPP_API_CALLS;

-- Check staging data
SELECT COUNT(*) FROM STAGING.STG_DEPARTURES;

-- Check analytics data
SELECT COUNT(*) FROM ANALYTICS.RELIABILITY_METRICS;
SELECT COUNT(*) FROM ANALYTICS.DEMAND_METRICS;
```

5. **Test chatbot queries:**
```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the on-time performance for Route 1?"}'
```

## 🚀 Step 11: Deploy to AWS (After Local Testing)

Once everything works locally:

1. **Export environment variables to AWS Secrets Manager (optional but recommended):**
```bash
# Load .env and export to AWS Secrets Manager
python scripts/load_env.py --export-aws --secret-name transit/system/env
```

2. **Deploy CloudFormation stack:**
```bash
cd infrastructure
aws cloudformation create-stack \
  --stack-name transit-system-dev \
  --template-body file://cloudformation.yaml \
  --parameters \
    ParameterKey=TransitAppAPIKey,ParameterValue=YOUR_API_KEY \
    ParameterKey=SnowflakeAccount,ParameterValue=YOUR_ACCOUNT.us-west-2 \
    ParameterKey=SnowflakeUser,ParameterValue=YOUR_USERNAME \
    ParameterKey=SnowflakePassword,ParameterValue=YOUR_PASSWORD \
    ParameterKey=Environment,ParameterValue=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile transit-system
```

2. **Deploy Lambda functions:**
```bash
cd ingestion/lambda

# Package and deploy ingestion Lambda
zip -r transit-api-ingestion.zip transit_api_ingestion.py utils.py
aws lambda update-function-code \
  --function-name transit-api-ingestion-dev \
  --zip-file fileb://transit-api-ingestion.zip \
  --profile transit-system

# Package and deploy GTFS sync Lambda
zip -r transit-gtfs-sync.zip gtfs_sync.py utils.py
aws lambda update-function-code \
  --function-name transit-gtfs-sync-dev \
  --zip-file fileb://transit-gtfs-sync.zip \
  --profile transit-system
```

3. **Setup Snowpipe** (follow Snowflake documentation to connect S3 to Snowpipe)

4. **Deploy Airflow DAGs** (if using AWS MWAA):
```bash
aws s3 sync airflow/dags/ s3://your-mwaa-dags-bucket/dags/ --profile transit-system
```

## ✅ Verification Checklist

After local testing, verify:

- [ ] `.env` file created and configured with all required values
- [ ] Environment variables loaded successfully (`source scripts/load_env.sh`)
- [ ] TransitApp API calls work (check API key in .env)
- [ ] Data can be uploaded to S3 (check AWS credentials and profile)
- [ ] Snowflake connection works (check credentials in .env)
- [ ] dbt can connect and run models (uses env vars from .env)
- [ ] Airflow DAGs can be parsed (no syntax errors)
- [ ] Chatbot can connect to OpenAI and Snowflake (uses env vars from .env)
- [ ] Dashboard queries return data (using ANALYTICS schema, not MARTS)

## 🐛 Troubleshooting

### Issue: "Unable to locate credentials"
**Solution:** Set AWS profile: `export AWS_PROFILE=transit-system` or configure AWS CLI

### Issue: "dbt connection failed"
**Solution:** Check `~/.dbt/profiles.yml` has correct Snowflake credentials

### Issue: "TransitApp API rate limit exceeded"
**Solution:** Wait 1 minute between calls (free tier: 5 calls/min)

### Issue: "Chatbot OpenAI API error"
**Solution:** Check API key is valid and has credits

### Issue: "Airflow DAG not showing"
**Solution:** Check DAG syntax, logs, and file permissions

## 📝 Notes

- **Local mode:** You can test most components locally without AWS deployment
- **S3 optional:** For local testing, you can save data to local files instead of S3
- **Snowpipe:** Only needed for production; local testing can use manual `COPY INTO` commands
- **Cost:** Local testing costs nothing; AWS free tier used only for deployment

## 🔗 Next Steps

After successful local testing:
1. Review [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
2. Deploy infrastructure via CloudFormation
3. Setup monitoring and alerts
4. Review [EXTENSION_ROADMAP.md](./EXTENSION_ROADMAP.md) for future enhancements

