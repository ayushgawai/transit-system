# Quick Start - Testing the Project

## Step 1: Load Secrets
```bash
cd /Users/spartan/Documents/MSDA/Project/transit-system
source scripts/load_secrets.sh
```

## Step 2: Test Locally (NO AWS COSTS)

### Test Data Ingestion
```bash
cd ingestion
python test_ingestion_local.py
```
This saves data to `data/local_test/` - **NO AWS costs**

### Test Snowflake Connection
```bash
cd ../dbt/transit_dbt
source /Users/spartan/Documents/GitHub/MSADI/.dbt_venv/bin/activate
source ../../scripts/load_secrets.sh
dbt debug
```

### Test Chatbot (Note: Cursor API key won't work - see below)
```bash
cd ../../chatbot
source ../scripts/load_secrets.sh
python chatbot_api.py
```

## Step 3: AWS Testing (MINIMAL COSTS - Free Tier)

**⚠️ Only test AWS after local testing works!**

### Deploy Infrastructure
```bash
cd infrastructure
source ../scripts/load_secrets.sh

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

### ⛔ STOP RESOURCES IMMEDIATELY AFTER TESTING
```bash
# See STOP_RESOURCES.md for cleanup commands
aws cloudformation delete-stack --stack-name transit-system-dev --profile transit-system
```

## AWS Free Tier Confirmation

✅ **All resources use AWS Free Tier:**
- S3: 5GB storage, 20K GET requests/month (FREE)
- Lambda: 1M requests/month, 400K GB-seconds (FREE)
- SQS: 1M requests/month (FREE)
- EventBridge: 1M custom events/month (FREE)
- CloudWatch Logs: 5GB ingestion (FREE)

⚠️ **Potential costs (minimal):**
- S3 storage beyond 5GB: ~$0.023/GB/month
- Snowflake: Free trial ($400 credits for 30 days), then pay-per-use
- Data transfer: Usually free within same region

## Chatbot API Key Issue

**Cursor API key will NOT work** - Cursor uses a different API endpoint.

**Options:**

1. **Use Ollama (Free, Local LLM)** - Recommended:
```bash
# Install Ollama
brew install ollama  # or download from https://ollama.ai

# Download model
ollama pull llama2

# Update chatbot_api.py to use Ollama instead of OpenAI
# (I can help you modify the code)
```

2. **Get OpenAI API Key** (Free tier available):
   - Sign up at https://platform.openai.com
   - Get free tier API key
   - Update `secrets.yaml` with real OpenAI key

3. **Disable Chatbot** (for now):
   - Just skip chatbot testing
   - Rest of the system works without it

See [TESTING.md](./TESTING.md) for detailed testing guide.

