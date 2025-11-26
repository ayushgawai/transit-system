# Test Steps - Transit System

## Step 1: Setup Virtual Environment
```bash
cd /Users/spartan/Documents/MSDA/Project/transit-system

# Create venv (if not already created)
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Load Secrets
```bash
# Make sure venv is activated
source venv/bin/activate

# Load secrets
source scripts/load_secrets.sh

# Verify secrets loaded
echo $SNOWFLAKE_ACCOUNT
echo $TRANSIT_APP_API_KEY
```

## Step 3: Test Local Data Ingestion (NO AWS COSTS)
```bash
# Make sure venv is activated
source venv/bin/activate

cd ingestion
python test_ingestion_local.py
```

**Expected:** Data saved to `data/local_test/` directory

**Verify:**
```bash
ls -la data/local_test/transitapp/
```

## Step 3: Test Snowflake Connection
```bash
cd ../dbt/transit_dbt
source /Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate
source ../../scripts/load_secrets.sh

# Test connection
dbt debug
```

**Expected:** "Connection test: [OK]" or similar success message

## Step 4: Test dbt Models (After Data is in Snowflake)

**First, make sure you have data in Snowflake RAW schema. If not, you can:**
- Manually load test data, OR
- Skip this step for now

```bash
# Run staging models
dbt run --select staging.*

# Run analytics models (if staging works)
dbt run --select analytics.*

# Test models
dbt test
```

## Step 6: (Optional) Test AWS Resources

**⚠️ Only if you want to test AWS. Remember to STOP resources after!**

```bash
cd ../../infrastructure
source ../scripts/load_secrets.sh

# Deploy stack
aws cloudformation create-stack \
  --stack-name transit-system-dev \
  --template-body file://cloudformation.yaml \
  --parameters \
    ParameterKey=TransitAppAPIKey,ParameterValue=$TRANSIT_APP_API_KEY \
    ParameterKey=SnowflakeAccount,ParameterValue=$SNOWFLAKE_ACCOUNT \
    ParameterKey=SnowflakeUser,ParameterValue=$SNOWFLAKE_USER \
    ParameterKey=SnowflakePassword,ParameterValue=$SNOWFLAKE_PASSWORD \
    ParameterKey=Environment,ParameterValue=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile transit-system

# Wait for stack creation (5-10 minutes)
aws cloudformation wait stack-create-complete --stack-name transit-system-dev --profile transit-system

# Test Lambda
aws lambda invoke \
  --function-name transit-api-ingestion-dev \
  --profile transit-system \
  response.json

# ⛔ STOP RESOURCES IMMEDIATELY
aws cloudformation delete-stack --stack-name transit-system-dev --profile transit-system
```

## Quick Test (Minimal - Just Verify Setup)
```bash
# 1. Activate venv and install dependencies
cd /Users/spartan/Documents/MSDA/Project/transit-system
source venv/bin/activate
pip install -r requirements.txt

# 2. Load secrets
source scripts/load_secrets.sh

# 3. Test ingestion (local)
cd ingestion
python test_ingestion_local.py

# 4. Test Snowflake
cd ../dbt/transit_dbt
source /Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate
source ../../scripts/load_secrets.sh
dbt debug
```

## Troubleshooting

**Issue: "Module not found"**
```bash
# Make sure venv is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Issue: "dbt not found"**
```bash
source /Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate
```

**Issue: "AWS credentials not found"**
```bash
aws configure --profile transit-system
```

**Issue: "Snowflake connection failed"**
- Check credentials in `secrets.yaml`
- Verify Snowflake account is correct format
- Test connection in Snowflake UI first

