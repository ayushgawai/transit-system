# Transit Service Reliability & Demand Planning System

A production-capable prototype for a metropolitan transit operator that ingests real-time and static transit data, processes it through a cloud streaming pipeline, builds analytical models, and provides decision-support dashboards and a natural language chatbot.

## 🎯 Key Features

- **Real-time Data Ingestion**: Streaming pipeline from TransitApp API and GTFS static feeds
- **Cloud-Native Architecture**: AWS serverless stack (Lambda, SQS, S3, EventBridge)
- **Data Warehouse**: Snowflake with Snowpipe for continuous loading
- **Data Transformation**: dbt Core for dimensional modeling and analytics marts
- **Orchestration**: Apache Airflow for workflow management
- **ML Forecasting**: Demand, delay, and crowding predictions using Snowflake ML
- **Interactive Dashboards**: BI tools (QuickSight/Snowsight) for visualization
- **Chatbot**: Natural language queries powered by LLM (OpenAI or local)
- **Infrastructure as Code**: CloudFormation templates for AWS resources
- **Cost-Aware**: Designed to operate within AWS Free Tier and Snowflake trial

## 🏗️ Architecture Overview

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system architecture and technology justifications.

## 📋 Prerequisites

Before starting, ensure you have:

1. **AWS Account** with Free Tier eligibility
2. **Snowflake Account** (free trial: $400 credits for 30 days)
3. **TransitApp API Key** (request at https://transit.land/api)
4. **Python 3.9+** installed locally
5. **Git** for version control
6. **Docker** (optional, for local Airflow)
7. **Node.js** (optional, for local Metabase if using)

## 🚀 Quick Start

### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd transit-system
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Master Config

1. Copy the master config template:
```bash
cp config/master_config.yaml config/config.yaml
```

2. Edit `config/config.yaml` and set:
   - `TRANSIT_APP_API_KEY`: Your TransitApp API key
   - `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`
   - `AWS_REGION`: Your preferred AWS region
   - Other environment-specific values

3. **Never commit `config/config.yaml`** to version control (already in `.gitignore`)

### Step 3: Deploy AWS Infrastructure

```bash
# Set AWS credentials (or use AWS CLI configure)
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>

# Deploy CloudFormation stack
cd infrastructure
aws cloudformation create-stack \
  --stack-name transit-system \
  --template-body file://cloudformation.yaml \
  --parameters ParameterKey=ConfigS3Path,ParameterValue=s3://your-bucket/config.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack creation (5-10 minutes)
aws cloudformation wait stack-create-complete --stack-name transit-system

# Get output values (S3 bucket names, SQS ARNs, etc.)
aws cloudformation describe-stacks --stack-name transit-system
```

### Step 4: Setup Snowflake

1. **Create Database and Schemas**:
```bash
cd snowflake
snowsql -a <account> -u <user> -f setup/schema.sql
```

2. **Create Storage Integration** (for Snowpipe):
```sql
-- Run in Snowflake worksheet
CREATE STORAGE INTEGRATION TRANSIT_S3_STORAGE_INTEGRATION
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<role-arn-from-cloudformation-output>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://<raw-bucket-name>/');
```

3. **Grant Permissions**:
```bash
snowsql -a <account> -u <user> -f setup/permissions.sql
```

4. **Create Snowpipe**:
```bash
snowsql -a <account> -u <user> -f setup/snowpipe.sql
```

### Step 5: Deploy Lambda Functions

```bash
cd ingestion/lambda

# Package ingestion Lambda
zip -r transit-api-ingestion.zip transit_api_ingestion.py utils.py
aws lambda update-function-code \
  --function-name transit-api-ingestion \
  --zip-file fileb://transit-api-ingestion.zip

# Package GTFS sync Lambda
zip -r transit-gtfs-sync.zip gtfs_sync.py utils.py
aws lambda update-function-code \
  --function-name transit-gtfs-sync \
  --zip-file fileb://transit-gtfs-sync.zip
```

### Step 6: Setup dbt Project

```bash
cd dbt/transit_dbt

# Install dbt-snowflake
pip install dbt-snowflake

# Configure profiles.yml (pointing to Snowflake)
# Edit ~/.dbt/profiles.yml or dbt/profiles.yml

# Test connection
dbt debug

# Run initial models
dbt seed  # Load reference data
dbt run  # Build staging and marts
dbt test  # Run data tests
```

### Step 7: Setup Airflow

**Option A: Local Airflow (for development)**

```bash
cd airflow

# Start Airflow via Docker Compose
docker-compose up -d

# Access Airflow UI at http://localhost:8080
# Default credentials: admin/admin (change in docker-compose.yml)
```

**Option B: AWS MWAA (for production)**

1. Create MWAA environment via AWS Console or CLI
2. Upload DAGs folder to S3:
```bash
aws s3 sync airflow/dags/ s3://your-mwaa-dags-bucket/dags/
```

3. Configure MWAA environment variables (Snowflake credentials, API keys)

### Step 8: Setup BI Dashboard

**Option A: Snowsight (Recommended - Free, Built-in)**

1. Log into Snowflake
2. Navigate to Snowsight (Worksheets)
3. Use SQL queries from `dashboard/snowsight_queries/` to build visualizations
4. Create dashboards using Snowsight's charting features

**Option B: Amazon QuickSight**

1. Create QuickSight account (free tier: 1 user, 10GB SPICE)
2. Connect to Snowflake data source
3. Import dashboard definitions from `dashboard/quicksight/`

**Option C: Metabase (Self-hosted)**

```bash
docker run -d -p 3000:3000 \
  -e MB_DB_TYPE=postgres \
  -e MB_DB_DBNAME=metabase \
  -e MB_DB_PORT=5432 \
  -e MB_DB_USER=metabase \
  -e MB_DB_PASS=metabase \
  metabase/metabase
```

1. Access Metabase at http://localhost:3000
2. Add Snowflake as data source
3. Import dashboard from `dashboard/metabase/transit_dashboard.json`

### Step 9: Deploy Chatbot

```bash
cd chatbot

# Install dependencies
pip install openai python-dotenv flask

# Set environment variables
export OPENAI_API_KEY=<your-key>
export SNOWFLAKE_ACCOUNT=<account>
export SNOWFLAKE_USER=<user>
export SNOWFLAKE_PASSWORD=<password>

# Run chatbot API server
python chatbot_api.py
```

Or deploy as Lambda function:

```bash
zip -r chatbot.zip chatbot_api.py utils.py
aws lambda create-function \
  --function-name transit-chatbot \
  --runtime python3.9 \
  --role <lambda-execution-role-arn> \
  --handler chatbot_api.handler \
  --zip-file fileb://chatbot.zip \
  --environment Variables={OPENAI_API_KEY=<key>,SNOWFLAKE_ACCOUNT=<account>}
```

## 📁 Project Structure

```
transit-system/
├── ARCHITECTURE.md              # System architecture documentation
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config/
│   ├── master_config.yaml       # Master configuration template
│   └── config.yaml             # Your local config (not in git)
├── infrastructure/
│   ├── cloudformation.yaml      # AWS IaC template
│   └── parameters.json          # CloudFormation parameters
├── ingestion/
│   ├── lambda/
│   │   ├── transit_api_ingestion.py  # TransitApp API Lambda
│   │   ├── gtfs_sync.py              # GTFS sync Lambda
│   │   └── utils.py                  # Shared utilities
│   └── scripts/
│       └── test_ingestion.py         # Local testing script
├── snowflake/
│   ├── setup/
│   │   ├── schema.sql               # Database schema
│   │   ├── snowpipe.sql             # Snowpipe setup
│   │   └── permissions.sql          # Role permissions
│   └── ml/
│       ├── demand_forecast.py       # Demand forecasting model
│       └── delay_forecast.py        # Delay forecasting model
├── dbt/
│   └── transit_dbt/
│       ├── dbt_project.yml
│       ├── profiles.yml
│       ├── models/
│       │   ├── staging/
│       │   └── marts/
│       ├── seeds/
│       └── tests/
├── airflow/
│   ├── dags/
│   │   ├── ingestion_dag.py
│   │   ├── transformation_dag.py
│   │   └── ml_refresh_dag.py
│   └── docker-compose.yml       # Local Airflow setup
├── dashboard/
│   ├── snowsight_queries/       # SQL for Snowsight
│   ├── quicksight/              # QuickSight definitions
│   └── metabase/                # Metabase dashboard JSON
├── chatbot/
│   ├── chatbot_api.py           # Flask/API Gateway endpoint
│   ├── llm_integration.py       # LLM query processing
│   └── snowflake_query_builder.py  # SQL generation from NL
└── tests/
    ├── unit/
    └── integration/
```

## 🔧 Configuration

All configuration is centralized in `config/config.yaml`. See `config/master_config.yaml` for documentation of all parameters.

Key configuration sections:
- **transit_app**: API keys, rate limits, agencies to monitor
- **aws**: Region, S3 buckets, Lambda settings
- **snowflake**: Account, credentials, schemas
- **airflow**: DAG schedules, dbt paths
- **ml**: Model configurations, retrain schedules
- **chatbot**: LLM provider, prompts, capabilities

## 📊 Data Model

### Raw Layer (Snowflake RAW schema)
- `raw.transitapp_api_calls` - JSON dumps from TransitApp API
- `raw.gtfs_routes` - GTFS routes static data
- `raw.gtfs_stops` - GTFS stops static data
- `raw.gtfs_trips` - GTFS trips/schedules

### Staging Layer (dbt STAGING schema)
- `staging.departures` - Cleaned departure data
- `staging.alerts` - Service alerts
- `staging.routes` - Route dimension
- `staging.stops` - Stop dimension
- `staging.trips` - Trip/schedule dimension

### Analytics Marts (dbt MARTS schema)
- `marts.reliability_metrics` - On-time performance, headway gaps
- `marts.demand_metrics` - Boardings by stop/route/time
- `marts.crowding_metrics` - Occupancy proxies, capacity utilization
- `marts.revenue_metrics` - Revenue impact by route/reliability
- `marts.forecasts` - ML predictions (demand, delays, crowding)
- `marts.decision_support` - Ranked recommendations

See `dbt/transit_dbt/models/` for detailed schema definitions.

## 📈 Dashboards

### Service Reliability Monitor
- **On-Time Performance**: Percentage of on-time departures by route
- **Headway Gaps**: Distribution of time between consecutive vehicles
- **Service Consistency**: Coefficient of variation for headways
- **Alert Frequency**: Number and duration of service disruptions

### Demand & Crowding Heatmap
- **Boarding Heatmap**: Boardings by stop and hour (heatmap visualization)
- **Route Popularity**: Top routes by total boardings
- **Time-of-Day Patterns**: Peak vs off-peak demand
- **Capacity Utilization**: Estimated occupancy % by route/stop

### Revenue Overlay Panel
- **Revenue by Route**: Total fare revenue (if available) or ridership proxy
- **Reliability Impact on Revenue**: Correlation between on-time performance and ridership
- **Cost per Passenger**: Operational cost efficiency metrics

### Forecasting Panel
- **Next 24h Demand Forecast**: Predicted boardings by hour
- **Delay Predictions**: Expected delays for next 48 hours
- **Crowding Forecast**: Expected capacity utilization

### Decision Support Table
- **Fleet Reallocation Suggestions**: Routes that would benefit from additional vehicles
- **Frequency Adjustment Recommendations**: Routes needing higher/lower frequency
- **Priority Actions**: Ranked list of operational improvements

## 🤖 Chatbot Examples

The chatbot supports natural language queries such as:

- "Which route tomorrow at 8am is likely to be most crowded?"
- "What's the on-time performance for Route 1 this week?"
- "Which stops have the highest boarding rates?"
- "Recommend fleet reallocation for tomorrow's morning rush"
- "Show me revenue impact of delays on Route 5"

See `chatbot/` for implementation details.

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires AWS/Snowflake access)
pytest tests/integration/ --aws-profile <profile>

# dbt tests
cd dbt/transit_dbt
dbt test
```

## 📊 Monitoring & Cost Management

### CloudWatch Dashboards
- Lambda invocations, errors, duration
- SQS queue depth
- S3 bucket sizes
- API Gateway requests (chatbot)

### Snowflake Monitoring
- Warehouse credit usage (query `SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`)
- Storage costs
- Query performance

### Cost Alerts
- AWS Budgets: Set $10/month budget with alerts at 80%, 100%
- CloudWatch alarms for unexpected usage spikes

See `monitoring/` for detailed monitoring setup.

## 🚀 Deployment Checklist

- [ ] AWS account set up with billing alerts
- [ ] Snowflake account created (free trial activated)
- [ ] TransitApp API key obtained
- [ ] Master config file configured (config.yaml)
- [ ] CloudFormation stack deployed successfully
- [ ] Snowflake database and schemas created
- [ ] Snowpipe configured and tested
- [ ] Lambda functions deployed and tested
- [ ] EventBridge schedules activated
- [ ] dbt project configured and models run successfully
- [ ] Airflow DAGs deployed and running
- [ ] BI dashboard connected and showing data
- [ ] Chatbot deployed and responding
- [ ] Monitoring and alerts configured
- [ ] Documentation reviewed

## 🔮 Future Extensions

See [EXTENSION_ROADMAP.md](./EXTENSION_ROADMAP.md) for detailed future enhancements including:

- Reinforcement learning for dynamic scheduling
- Real-time passenger push notifications
- Dynamic demand-based pricing
- Mobile rider app integration
- Advanced anomaly detection
- Multi-agency federation

## 📝 License

MIT License - see LICENSE file

## 🤝 Contributing

1. Create feature branch from `main`
2. Make changes following code style guidelines
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## 📧 Support

For issues or questions, please open an issue in the GitHub repository.

## 🙏 Acknowledgments

- TransitApp for transit data API
- GTFS community for open transit data standards
- AWS, Snowflake, dbt, Airflow communities for excellent tools

