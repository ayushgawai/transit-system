# Testing Guide - Transit System

## ⚠️ IMPORTANT: Cost Management

**Before Testing:**
- All AWS resources are designed for **Free Tier** where possible
- **STOP ALL RESOURCES** after testing to avoid charges
- Monitor AWS Billing Dashboard during testing
- Set up billing alerts (see below)

**Free Tier Resources Used:**
- ✅ S3: 5GB storage, 20K GET requests/month (FREE)
- ✅ Lambda: 1M requests/month, 400K GB-seconds (FREE)
- ✅ SQS: 1M requests/month (FREE)
- ✅ EventBridge: 1M custom events/month (FREE)
- ✅ CloudWatch Logs: 5GB ingestion, 5GB storage (FREE)

**Resources That May Incur Costs:**
- ⚠️ Snowflake: Free trial ($400 credits for 30 days), then pay-per-use
- ⚠️ S3 storage beyond 5GB: ~$0.023/GB/month
- ⚠️ Lambda beyond free tier: Very minimal (unlikely to exceed)
- ⚠️ Data transfer: Usually free within same region

## 🧪 Local Testing (NO AWS COSTS)

**Test everything locally first before deploying to AWS!**

### Step 1: Load Secrets
```bash
cd /Users/spartan/Documents/MSDA/Project/transit-system
source scripts/load_secrets.sh
```

### Step 2: Test Data Ingestion (Local - No AWS)
```bash
cd ingestion
python test_ingestion_local.py
```
This saves data locally - **NO AWS costs**

### Step 3: Test Snowflake Connection
```bash
# Test dbt connection
cd dbt/transit_dbt
source /Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate
source ../../scripts/load_secrets.sh
dbt debug
```

### Step 4: Test Chatbot (Local - No AWS)
```bash
cd chatbot
source ../scripts/load_secrets.sh
python chatbot_api.py
# Test in another terminal:
curl -X POST http://localhost:5000/health
```

## ☁️ AWS Testing (Minimal Costs)

**Only deploy to AWS after local testing works!**

### Step 1: Set Up Billing Alerts
```bash
# Create billing alarm (FREE)
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://infrastructure/budget.json \
  --notifications-with-subscribers file://infrastructure/budget-notifications.json \
  --profile transit-system
```

Or manually in AWS Console:
1. Go to AWS Billing Dashboard
2. Set up billing alert for $5 threshold
3. Enable email notifications

### Step 2: Deploy Infrastructure (One-time)
```bash
cd infrastructure
source ../scripts/load_secrets.sh

# Deploy CloudFormation stack
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
```

### Step 3: Test AWS Resources
```bash
# Test Lambda functions
aws lambda invoke \
  --function-name transit-api-ingestion-dev \
  --profile transit-system \
  response.json

# Check S3 bucket
aws s3 ls s3://transit-raw-data-436204347796/ --profile transit-system
```

### Step 4: ⛔ STOP ALL RESOURCES AFTER TESTING

**CRITICAL: Run these commands after testing to avoid charges:**

```bash
# Delete CloudFormation stack (stops all resources)
aws cloudformation delete-stack \
  --stack-name transit-system-dev \
  --profile transit-system

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name transit-system-dev \
  --profile transit-system

# Verify deletion
aws cloudformation describe-stacks \
  --stack-name transit-system-dev \
  --profile transit-system 2>&1 | grep "does not exist" && echo "✅ Stack deleted successfully"
```

**Manual Cleanup Checklist:**
- [ ] CloudFormation stack deleted
- [ ] S3 buckets empty and deleted (if not auto-deleted)
- [ ] Lambda functions deleted
- [ ] EventBridge rules disabled/deleted
- [ ] CloudWatch logs cleaned up (optional)
- [ ] Snowflake warehouse suspended (in Snowflake UI)

## 🔄 Quick Test Workflow

```bash
# 1. Load secrets
source scripts/load_secrets.sh

# 2. Test locally (NO COST)
cd ingestion && python test_ingestion_local.py
cd ../chatbot && python chatbot_api.py

# 3. Test Snowflake (uses free trial credits)
cd ../dbt/transit_dbt
dbt debug
dbt run --select staging.*

# 4. Deploy to AWS (MINIMAL COST)
cd ../../infrastructure
# ... deploy commands above ...

# 5. ⛔ STOP RESOURCES IMMEDIATELY
# ... cleanup commands above ...
```

## 📊 Cost Monitoring

**Check costs during testing:**
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +"%Y-%m-01"),End=$(date -u +"%Y-%m-%d") \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --profile transit-system
```

**Snowflake Credit Usage:**
```sql
-- Run in Snowflake
SELECT 
    DATE_TRUNC('day', START_TIME) as date,
    SUM(CREDITS_USED) as credits_used
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= CURRENT_DATE - 7
GROUP BY DATE_TRUNC('day', START_TIME)
ORDER BY date DESC;
```

## 🚨 Emergency Stop

If you see unexpected charges:

```bash
# Delete everything immediately
aws cloudformation delete-stack --stack-name transit-system-dev --profile transit-system

# Suspend Snowflake warehouse
# Run in Snowflake: ALTER WAREHOUSE TRANSIT_WH SUSPEND;

# Empty and delete S3 buckets
aws s3 rm s3://transit-raw-data-436204347796 --recursive --profile transit-system
aws s3 rb s3://transit-raw-data-436204347796 --profile transit-system
```

## 📝 Testing Checklist

- [ ] Secrets loaded successfully
- [ ] Local ingestion test passes
- [ ] Snowflake connection works
- [ ] dbt models run successfully
- [ ] Chatbot API responds
- [ ] AWS resources deployed (if testing AWS)
- [ ] **ALL AWS RESOURCES STOPPED AFTER TESTING** ⛔
- [ ] Billing checked - no unexpected charges

