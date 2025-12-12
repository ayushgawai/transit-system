# Transit Service Reliability & Demand Planning System

**MSDA Capstone Project** - Production-capable prototype for metropolitan transit operators

**Team Members:**
- Ayush Gawai
- Khushi Donda
- Aryan Choudhari
- Bhoomika Lnu
- Group 9

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Data Flow](#data-flow)
5. [Quick Start](#quick-start)
6. [Component Details](#component-details)
7. [Configuration](#configuration)
8. [API Documentation](#api-documentation)
9. [Frontend Pages](#frontend-pages)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

This system provides a comprehensive solution for transit operators to:
- **Monitor real-time transit performance** with live departure tracking
- **Analyze historical patterns** using GTFS schedule data
- **Forecast demand** using machine learning models
- **Query data interactively** using natural language via LLM integration
- **Visualize insights** through interactive dashboards and maps

The system processes data from multiple sources:
- **GTFS Feeds**: Static schedule data from BART and VTA
- **Transit API**: Real-time departure data via streaming pipeline
- **Historical Data**: Processed analytics for trend analysis

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   GTFS Feeds    │     │  Transit API    │
│  (BART, VTA)    │     │  (Real-time)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │                       │
    ┌────▼───────────────────────▼────┐
    │      Airflow Orchestration      │
    │  ┌───────────────────────────┐   │
    │  │ gtfs_incremental_dag     │   │
    │  │ transit_streaming_dag    │   │
    │  │ ml_forecast_dag          │   │
    │  └──────────────────────────┘   │
    └──────────────┬───────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ┌────▼────┐        ┌────▼────┐
    │  Kafka  │        │   dbt   │
    │Producer │        │ Models  │
    └────┬────┘        └────┬────┘
         │                  │
    ┌────▼────┐            │
    │  Kafka  │            │
    │Consumer │            │
    └────┬────┘            │
         │                  │
         └────────┬──────────┘
                  │
         ┌────────▼────────┐
         │    Snowflake    │
         │  Data Warehouse │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  FastAPI Backend│
         │  + Perplexity   │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  React Frontend │
         │  (Vite + TS)    │
         └─────────────────┘
```

### Component Layers

1. **Data Ingestion Layer**
   - GTFS incremental ingestion (Airflow DAG)
   - Real-time streaming via Kafka (Producer → Consumer)
   - Data landing in Snowflake `LANDING` schema

2. **Data Transformation Layer**
   - dbt models for data cleaning and standardization
   - Schema: `ANALYTICS_RAW` → `ANALYTICS_TRANSFORM` → `ANALYTICS_ANALYTICS`
   - Incremental and full refresh strategies

3. **Machine Learning Layer**
   - Snowflake ML FORECAST models
   - Demand forecasting (route-level predictions)
   - Delay forecasting (when sufficient data available)
   - Results stored in `ANALYTICS_ML` schema

4. **API Layer**
   - FastAPI REST endpoints
   - Perplexity LLM integration for natural language queries
   - AWS Secrets Manager for credential management
   - Real-time data serving to frontend

5. **Presentation Layer**
   - React + TypeScript frontend
   - Vite build tool
   - Interactive dashboards, maps, charts
   - Real-time data visualization

---

## Technology Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Core programming language |
| **FastAPI** | Latest | REST API framework |
| **Snowflake** | Cloud | Data warehouse |
| **Apache Airflow** | 2.x | Workflow orchestration |
| **Apache Kafka** | Latest | Streaming data pipeline |
| **dbt (data build tool)** | 1.x | Data transformation |
| **Perplexity AI** | API | LLM for natural language queries |
| **AWS Secrets Manager** | Cloud | Secure credential storage |
| **Docker** | Latest | Containerization |
| **Docker Compose** | Latest | Multi-container orchestration |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.2.0 | UI framework |
| **TypeScript** | Latest | Type-safe JavaScript |
| **Vite** | Latest | Build tool and dev server |
| **Tailwind CSS** | Latest | Utility-first CSS |
| **Recharts** | 2.10.3 | Chart library |
| **React Leaflet** | 4.2.1 | Map visualization |
| **React Router** | 6.20.0 | Client-side routing |

### Infrastructure

| Component | Purpose |
|-----------|---------|
| **Docker Compose** | Local development environment |
| **PostgreSQL** | Airflow metadata database |
| **Zookeeper** | Kafka coordination |
| **AWS CLI** | Secrets Manager access |

---

## Data Flow

### 1. GTFS Data Pipeline

```
GTFS Feeds (BART, VTA)
    ↓
[Airflow: gtfs_incremental_dag]
    ↓
fetch_gtfs_incremental.py
    ↓
Snowflake LANDING.LANDING_GTFS_* tables
    ↓
[dbt: landing_to_raw models]
    ↓
ANALYTICS_RAW.STG_GTFS_* tables
    ↓
[dbt: transform models]
    ↓
ANALYTICS_TRANSFORM.ROUTE_DEPARTURES
    ↓
[dbt: analytics models]
    ↓
ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE
```

### 2. Streaming Data Pipeline

```
Transit API (Real-time departures)
    ↓
[Airflow: transit_streaming_dag]
    ↓
kafka_streaming_producer.py
    ↓
Kafka Topic: transit-streaming
    ↓
kafka_consumer_to_landing.py
    ↓
Snowflake LANDING.LANDING_STREAMING_DEPARTURES
    ↓
[dbt: streaming_to_analytics models]
    ↓
ANALYTICS_RAW.STG_STREAMING_DEPARTURES
    ↓
[Used in analytics models]
```

### 3. ML Forecasting Pipeline

```
ANALYTICS_TRANSFORM.ROUTE_DEPARTURES
    ↓
[Airflow: ml_forecast_dag]
    ↓
Snowflake ML FORECAST Model Creation
    ↓
Training on historical data (90 days)
    ↓
Forecast Generation (7 days ahead)
    ↓
ANALYTICS_ML.DEMAND_FORECAST
    ↓
[API: /api/forecasts/demand]
    ↓
[Frontend: Forecasts page]
```

### 4. Query Flow (LLM Integration)

```
User Question (Frontend)
    ↓
[API: /api/chat]
    ↓
chat_handler.py
    ↓
Perplexity LLM (with schema context)
    ↓
SQL Query Generation
    ↓
Snowflake Query Execution
    ↓
Response Formatting
    ↓
User Answer (Frontend)
```

---

## Quick Start

> **📖 For detailed setup instructions, see [SETUP.md](SETUP.md)**  
> **✅ Verified portable - see [PORTABILITY.md](PORTABILITY.md) for details**

### Prerequisites

1. **Docker Desktop** installed and running
2. **Python 3.9+** installed
3. **Node.js 18+** and npm installed
4. **AWS CLI** configured with profile `transit-system`
5. **Snowflake account** with credentials in AWS Secrets Manager

### AWS Secrets Manager Setup

Store Snowflake credentials:

```bash
aws secretsmanager create-secret \
  --name transit/snowflake-dev \
  --secret-string '{
    "account": "your-account.us-west-2",
    "user": "your-user",
    "password": "your-password",
    "warehouse": "HORNET_QUERY_WH",
    "database": "USER_DB_HORNET",
    "role": "TRAINING_ROLE"
  }'
```

Store Perplexity API key:

```bash
aws secretsmanager create-secret \
  --name transit/perplexity \
  --secret-string '{
    "api_key": "your-perplexity-api-key"
  }'
```

### One-Command Start

```bash
./start_all.sh
```

This script:
1. Starts Docker services (Kafka, Zookeeper, Airflow)
2. Starts Backend API (FastAPI on port 8000)
3. Starts Frontend (Vite dev server on port 3000)

### Manual Start (Alternative)

**Terminal 1 - Docker Services:**
```bash
./start_local.sh
```

**Terminal 2 - Backend:**
```bash
cd api
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd ui
npm run dev
```

### Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin`

### Initial Data Load

1. Open Airflow UI: http://localhost:8080
2. Find `gtfs_incremental_ingestion` DAG
3. Click "Trigger DAG" (play button)
4. Wait for completion (~5-10 minutes)
5. Trigger `transit_streaming` DAG for real-time data
6. Run dbt models: `cd dbt/transit_dbt && dbt run --target snowflake`
7. Trigger `ml_forecast_dag` for ML forecasts

### Stop All Services

```bash
./stop_all.sh
```

---

## Component Details

### 1. Apache Airflow

**Purpose**: Orchestrates all data pipelines

**DAGs**:
- `gtfs_incremental_ingestion`: Fetches GTFS data every 6 hours
- `transit_streaming`: Runs Kafka producer/consumer hourly
- `ml_forecast_dag`: Creates and trains ML models every 6 hours

**Location**: `airflow/dags/`

**Configuration**: 
- Uses LocalExecutor
- PostgreSQL metadata database
- Docker-based deployment

**Key Features**:
- Automatic retries
- Dependency management
- Task logging
- Web UI for monitoring

### 2. Apache Kafka

**Purpose**: Real-time data streaming

**Components**:
- **Producer** (`kafka_streaming_producer.py`): Fetches Transit API data → Kafka topic
- **Consumer** (`kafka_consumer_to_landing.py`): Kafka topic → Snowflake landing tables

**Configuration**:
- Topic: `transit-streaming`
- Bootstrap servers: `localhost:9092`
- Consumer group: `transit-consumers`

**Data Flow**:
1. Producer polls Transit API every 5 minutes
2. Messages sent to Kafka topic
3. Consumer reads messages and inserts to Snowflake
4. Data available in `LANDING.LANDING_STREAMING_DEPARTURES`

### 3. dbt (data build tool)

**Purpose**: Transform and model data

**Project Structure**:
```
dbt/transit_dbt/
├── models/
│   ├── landing_to_raw/      # Clean GTFS data
│   ├── streaming_to_analytics/  # Clean streaming data
│   ├── transform/            # Business logic
│   ├── analytics/            # Final metrics
│   └── ml_forecasts/         # ML model inputs
├── dbt_project.yml
└── profiles.yml
```

**Schemas**:
- `ANALYTICS_RAW`: Cleaned raw data (staging)
- `ANALYTICS_TRANSFORM`: Business transformations
- `ANALYTICS_ANALYTICS`: Final analytics tables
- `ANALYTICS_ML`: ML model training data

**Materialization Strategies**:
- `table`: For large, frequently queried data
- `view`: For lightweight transformations
- `incremental`: For append-only data

**Run Commands**:
```bash
cd dbt/transit_dbt
dbt run --target snowflake
dbt test --target snowflake
dbt docs generate --target snowflake
```

### 4. Snowflake Data Warehouse

**Purpose**: Central data storage and processing

**Database**: `USER_DB_HORNET`

**Schemas**:
- `LANDING`: Raw ingested data
- `ANALYTICS_RAW`: Cleaned staging data
- `ANALYTICS_TRANSFORM`: Transformed data
- `ANALYTICS_ANALYTICS`: Final analytics
- `ANALYTICS_ML`: ML models and forecasts

**Key Tables**:
- `LANDING.LANDING_GTFS_*`: Raw GTFS data
- `LANDING.LANDING_STREAMING_DEPARTURES`: Real-time departures
- `ANALYTICS_RAW.STG_GTFS_*`: Cleaned GTFS
- `ANALYTICS_RAW.STG_STREAMING_DEPARTURES`: Cleaned streaming
- `ANALYTICS_TRANSFORM.ROUTE_DEPARTURES`: Enriched departures
- `ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE`: Route metrics
- `ANALYTICS_ML.DEMAND_FORECAST`: ML predictions

**Snowflake ML**:
- Uses `SNOWFLAKE.ML.FORECAST` for time-series forecasting
- Models: `DEMAND_FORECAST_MODEL`, `DELAY_FORECAST_MODEL`
- Training on 90 days of historical data
- Forecasts 7 days ahead

### 5. FastAPI Backend

**Purpose**: REST API for frontend

**Location**: `api/main.py`

**Key Endpoints**:
- `GET /api/health`: Health check
- `GET /api/kpis`: Key performance indicators
- `GET /api/routes`: Route information
- `GET /api/live-data`: Real-time departures
- `GET /api/forecasts/demand`: ML demand forecasts
- `POST /api/chat`: LLM-powered queries
- `GET /api/admin/status`: System status

**Features**:
- CORS enabled for frontend
- Snowflake connection pooling
- Error handling and logging
- OpenAPI documentation at `/docs`

**LLM Integration**:
- Uses Perplexity AI API
- Schema-aware SQL generation
- Natural language to SQL conversion
- Response formatting for users

### 6. React Frontend

**Purpose**: User interface

**Location**: `ui/src/`

**Pages**:
- `Dashboard`: Overview KPIs
- `Routes`: Route details and performance
- `Analytics`: Historical analysis
- `MapView`: Geographic visualization
- `Forecasts`: ML predictions
- `LiveData`: Real-time departures
- `DataQuery`: LLM chat interface
- `BIDashboard`: Business intelligence views
- `Admin`: System administration

**Technologies**:
- React 18 with TypeScript
- Vite for fast development
- Tailwind CSS for styling
- Recharts for charts
- React Leaflet for maps
- React Router for navigation

**API Integration**:
- Base URL: `http://localhost:8000/api`
- Auto-refresh for live data (30 seconds)
- Error handling and loading states

### 7. AWS Secrets Manager

**Purpose**: Secure credential storage

**Secrets**:
- `transit/snowflake-dev`: Snowflake credentials
- `transit/perplexity`: Perplexity API key

**Access**:
- Backend loads secrets at startup
- Uses AWS CLI profile: `transit-system`
- Region: `us-west-2`

**Configuration**:
```python
from config.warehouse_config import get_warehouse_config
config = get_warehouse_config()
secrets = config._load_secrets()
```

### 8. Perplexity LLM Integration

**Purpose**: Natural language data queries

**Location**: `api/llm/chat_handler.py`

**How It Works**:
1. User asks question in natural language
2. System provides Snowflake schema context to LLM
3. LLM generates SQL query
4. Query executed against Snowflake
5. Results formatted and returned to user

**Schema Context**:
- Table definitions
- Column descriptions
- Sample queries
- Data availability info

**Example Queries**:
- "Show me reliability scores by route for VTA"
- "What are the busiest stops?"
- "Which routes have the most delays?"

---

## Configuration

### config.yaml

Main configuration file:

```yaml
warehouse:
  type: 'snowflake'  # or 'redshift'
  snowflake:
    account: ''  # From Secrets Manager
    user: ''     # From Secrets Manager
    password: '' # From Secrets Manager
    warehouse: 'HORNET_QUERY_WH'
    database: 'USER_DB_HORNET'
    role: 'TRAINING_ROLE'
    schema: 'ANALYTICS'

data_sources:
  gtfs:
    initial_load_date: '2025-08-01'
    incremental: true
  transit_api:
    streaming_enabled: true
    kafka_topic: 'transit-streaming'

airflow:
  schedule_interval_gtfs: '0 */6 * * *'  # Every 6 hours
  schedule_interval_streaming: '0 * * * *'  # Every hour
```

### dbt Configuration

`dbt/transit_dbt/profiles.yml`:
```yaml
transit_dbt:
  target: snowflake
  outputs:
    snowflake:
      type: snowflake
      account: ${SNOWFLAKE_ACCOUNT}
      user: ${SNOWFLAKE_USER}
      password: ${SNOWFLAKE_PASSWORD}
      warehouse: HORNET_QUERY_WH
      database: USER_DB_HORNET
      schema: ANALYTICS
      role: TRAINING_ROLE
```

---

## API Documentation

### Key Endpoints

#### GET /api/health
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "transit-ops-api"
}
```

#### GET /api/kpis
Get key performance indicators.

**Query Parameters**:
- `agency` (optional): Filter by agency (VTA, BART)

**Response**:
```json
{
  "success": true,
  "data": {
    "reliability": {
      "avg_on_time": 95.0,
      "avg_reliability": 90.0,
      "active_routes": 150,
      "total_departures": 50000
    },
    "demand": {
      "total_departures": 50000,
      "peak_hour": 8,
      "peak_departures": 5000
    }
  }
}
```

#### GET /api/live-data
Get real-time departure data.

**Query Parameters**:
- `agency` (optional): Filter by agency

**Response**:
```json
{
  "success": true,
  "data": {
    "departures": [...],
    "stats": {
      "total_today": 1000,
      "streaming_count": 1000,
      "realtime_count": 1000,
      "realtime_pct": 100.0,
      "avg_delay": -99.0,
      "on_time_count": 457,
      "on_time_pct": 45.7
    }
  }
}
```

#### GET /api/forecasts/demand
Get ML demand forecasts.

**Query Parameters**:
- `hours` (optional): Forecast window (6, 24, 168)
- `agency` (optional): Filter by agency

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "route_id": "123",
      "route_short_name": "22",
      "agency": "VTA",
      "forecast_date": "2025-12-10",
      "predicted_departures": 150,
      "forecast_generated_at": "2025-12-09T10:00:00Z"
    }
  ]
}
```

#### POST /api/chat
Natural language query endpoint.

**Request Body**:
```json
{
  "message": "Show me reliability scores by route for VTA"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "response": "Here are the reliability scores...",
    "data": [...]
  }
}
```

Full API documentation available at: http://localhost:8000/docs

---

## Frontend Pages

### Dashboard (`/`)
- Overview KPIs
- Real-time metrics
- Quick stats cards
- System status

### Routes (`/routes`)
- Route listing
- Route performance metrics
- Filter by agency
- Route details

### Analytics (`/analytics`)
- Historical trends
- Performance charts
- Time-series analysis
- Comparative metrics

### Map View (`/map`)
- Interactive map
- Stop locations
- Route visualization
- Real-time markers

### Forecasts (`/forecasts`)
- ML demand forecasts
- Forecast charts
- Time horizon selection
- Agency filtering

### Live Data (`/live-data`)
- Real-time departures table
- Delay severity distribution
- Departures by hour
- Data freshness indicators

### Data Query (`/query`)
- LLM chat interface
- Natural language queries
- Query history
- Response formatting

### BI Dashboard (`/bi-dashboard`)
- Business intelligence views
- Preset dashboards
- Export capabilities

### Admin (`/admin`)
- System status
- Table information
- Data quality metrics
- Pipeline health

---

## Troubleshooting

### Docker Services Not Starting

```bash
# Check Docker status
docker info

# Restart Docker services
docker-compose -f docker-compose.local.yml --profile local down -v
docker-compose -f docker-compose.local.yml --profile local up -d
```

### Backend Connection Errors

1. Check AWS credentials:
```bash
aws configure list --profile transit-system
```

2. Verify Secrets Manager:
```bash
aws secretsmanager get-secret-value --secret-id transit/snowflake-dev --profile transit-system
```

3. Check Snowflake connection:
```python
from api.warehouse_connection import get_warehouse_connection
with get_warehouse_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    print(cursor.fetchone())
```

### Frontend Not Loading

1. Check if backend is running:
```bash
curl http://localhost:8000/health
```

2. Check frontend logs:
```bash
tail -f logs/frontend.log
```

3. Clear node_modules and reinstall:
```bash
cd ui
rm -rf node_modules package-lock.json
npm install
```

### Airflow DAGs Failing

1. Check DAG logs in Airflow UI
2. Verify Python dependencies in Airflow container:
```bash
docker-compose -f docker-compose.local.yml exec airflow-webserver pip list
```

3. Check Snowflake connectivity from Airflow:
```bash
docker-compose -f docker-compose.local.yml exec airflow-webserver python -c "from api.warehouse_connection import get_warehouse_connection; conn = get_warehouse_connection(); print('Connected')"
```

### Kafka Issues

1. Check Kafka status:
```bash
docker-compose -f docker-compose.local.yml ps kafka
```

2. View Kafka logs:
```bash
docker-compose -f docker-compose.local.yml logs kafka
```

3. Restart Kafka:
```bash
docker-compose -f docker-compose.local.yml restart kafka zookeeper
```

### dbt Errors

1. Check dbt connection:
```bash
cd dbt/transit_dbt
dbt debug --target snowflake
```

2. Run with verbose logging:
```bash
dbt run --target snowflake --debug
```

3. Check model compilation:
```bash
dbt compile --target snowflake
```

---

## Best Practices

### Data Quality

1. **Incremental Models**: Use incremental materialization for large tables
2. **Data Validation**: Add dbt tests for data quality
3. **Error Handling**: Implement retry logic in Airflow tasks
4. **Monitoring**: Set up alerts for pipeline failures

### Performance

1. **Query Optimization**: Use appropriate indexes and clustering keys
2. **Caching**: Cache frequently accessed data in frontend
3. **Connection Pooling**: Reuse database connections
4. **Batch Processing**: Process data in batches for efficiency

### Security

1. **Secrets Management**: Never hardcode credentials
2. **Access Control**: Use Snowflake roles for data access
3. **API Authentication**: Add authentication for production
4. **CORS Configuration**: Restrict CORS to known origins

### Code Organization

1. **Modular Design**: Separate concerns (ingestion, transformation, serving)
2. **Documentation**: Document all functions and endpoints
3. **Version Control**: Use Git for all code
4. **Testing**: Write tests for critical functions

### Monitoring

1. **Logging**: Log all important events
2. **Metrics**: Track key metrics (API response times, data freshness)
3. **Alerts**: Set up alerts for failures
4. **Dashboards**: Monitor system health in Admin page

---

## Additional Resources

- **Table Reference**: See `TABLES_REFERENCE.md` for complete table documentation
- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **dbt Documentation**: Run `dbt docs generate --target snowflake` and open `target/index.html`
- **Airflow Documentation**: https://airflow.apache.org/docs/

---

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review Airflow task logs
3. Check Snowflake query history
4. Review this README and troubleshooting section

---

**Last Updated**: December 2025
**Version**: 1.0.0
