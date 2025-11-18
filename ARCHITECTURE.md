# Transit Service Reliability & Demand Planning System - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Sources                                 │
├─────────────────────────────────────────────────────────────────────┤
│  TransitApp API (v3)          │  GTFS Static Feeds (Public Open Data)│
│  - Real-time departures       │  - Routes, stops, schedules          │
│  - Alerts                     │  - Shapes, calendar                  │
│  - Stop/route info            │                                      │
└───────────────┬───────────────────────────┬─────────────────────────┘
                │                           │
                ▼                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS Streaming Ingestion Layer                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │ EventBridge  │─────▶│  SQS Queue   │─────▶│ Lambda Func  │    │
│  │  Scheduler   │      │   (Buffer)   │      │  (Ingestion) │    │
│  └──────────────┘      └──────────────┘      └──────┬───────┘    │
│                                                      │            │
│  ┌──────────────┐                                    ▼            │
│  │ Lambda Func  │                            ┌──────────────┐    │
│  │ (GTFS Sync)  │                            │   S3 Bucket  │    │
│  └──────┬───────┘                            │  (Raw Layer) │    │
│         │                                    └──────────────┘    │
│         └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Snowflake Data Warehouse                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │  Snowpipe    │─────▶│  Raw Schema  │─────▶│ Staging      │    │
│  │  (Auto-load) │      │  (Landing)   │      │  (dbt)       │    │
│  └──────────────┘      └──────────────┘      └──────┬───────┘    │
│                                                      │            │
│                                              ┌───────┴───────┐    │
│                                              │               │    │
│                                      ┌───────▼──────┐ ┌──────▼──┐ │
│                                      │   Analytics  │ │  ML     │ │
│                                      │   Marts      │ │ Models  │ │
│                                      └──────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────┐  ┌──────────────┐  ┌──────────────┐
│   Airflow Orchestration │  │ BI Dashboard │  │   Chatbot    │
│   - Ingestion DAGs      │  │ (QuickSight/ │  │   (LLM API)  │
│   - dbt Transform DAGs  │  │  Snowsight)  │  │              │
│   - ML Model Refresh    │  │              │  │              │
└─────────────────────────┘  └──────────────┘  └──────────────┘
```

## Technology Stack & Justification

### AWS Services
- **SQS (Simple Queue Service)**: Decouples ingestion Lambda from TransitApp API calls. Free tier: 1M requests/month. Lightweight alternative to Kinesis for our 5 calls/min rate limit.
- **Lambda**: Serverless compute for ingestion. Free tier: 1M requests/month, 400K GB-seconds. Perfect for periodic API calls and S3 uploads.
- **EventBridge (formerly CloudWatch Events)**: Scheduled triggers for periodic ingestion (every 5-10 minutes). Free tier: 1M custom events/month.
- **S3**: Durable storage for raw data. Free tier: 5GB storage, 20K GET requests/month. Standard tier for staging before Snowpipe.
- **Why not Kinesis?**: Kinesis has more overhead and costs more. For 5 calls/min, SQS+Lambda is sufficient and cheaper.

### Snowflake
- **Why Snowflake?**: 
  - Native Snowpipe for streaming ingestion from S3
  - Built-in ML capabilities (Snowpark ML)
  - Excellent SQL performance and data sharing
  - Free trial: $400 credits for 30 days, then limited free tier
  - Native BI integration (Snowsight)

### Apache Airflow
- **Why Airflow?**:
  - Open-source, industry standard for data orchestration
  - Rich scheduling and dependency management
  - Free to run (self-hosted or AWS MWAA free tier for 1st month)
  - dbt integration via dbt-cloud operator or bash operators

### dbt (Data Build Tool)
- **Why dbt?**:
  - SQL-based transformation layer
  - Version control for data models
  - Built-in testing and documentation
  - Modular, maintainable transformations
  - Native Snowflake connector
  - Free (Core version)

## Data Flow

1. **Ingestion**: 
   - EventBridge triggers Lambda every 5 minutes (respecting 5 calls/min limit)
   - Lambda calls TransitApp API, writes JSON to S3 raw bucket
   - GTFS sync Lambda runs daily, downloads static feeds, writes to S3

2. **Loading**:
   - Snowpipe monitors S3 bucket, auto-loads new files into Snowflake raw schema
   - Event notifications via SQS trigger Snowpipe (or auto-ingest if enabled)

3. **Transformation**:
   - Airflow DAG triggers dbt run after Snowpipe completes
   - dbt stages data, builds dimensional model (fact and dimension tables)
   - Creates analytics marts for specific use cases (reliability, demand, revenue)

4. **Analytics & ML**:
   - Snowflake ML models run on scheduled basis (via Airflow)
   - Forecasts demand, crowding, delays for next 24-48 hours
   - Results stored in marts for dashboard consumption

5. **Visualization & Decision Support**:
   - QuickSight/Snowsight connects to Snowflake marts
   - Real-time dashboards show reliability metrics, demand heatmaps
   - Chatbot queries Snowflake via LLM, provides natural language insights

## Key Differentiators

Beyond standard transit apps, this system provides:

1. **Route-Level Reliability Metrics**: On-time performance, headway gaps, service consistency
2. **Demand & Crowding Insights**: Which stops/routes/times are busiest, capacity utilization
3. **Revenue Overlay**: Link service reliability & ridership to financial impact
4. **Forecasting**: ML-based predictions for next-day demand, crowding, delays
5. **Decision Support**: Ranked suggestions for fleet reallocation, frequency adjustments
6. **Operational Intelligence**: Historical trends, anomaly detection, service optimization recommendations

