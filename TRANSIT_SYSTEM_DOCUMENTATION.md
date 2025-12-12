# Transit Service Reliability & Demand Planning System
## Comprehensive Technical Documentation

**Project**: MSDA Capstone Project  
**Team**: Group 9  
**Members**: Ayush Gawai, Khushi Donda, Aryan Choudhari, Bhoomika Lnu  
**Date**: December 2025  
**Version**: 1.0.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Introduction](#2-introduction)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Data Sources and Ingestion](#5-data-sources-and-ingestion)
6. [Data Transformation Pipeline](#6-data-transformation-pipeline)
7. [Machine Learning Pipeline](#7-machine-learning-pipeline)
8. [API and Backend Services](#8-api-and-backend-services)
9. [Frontend Application](#9-frontend-application)
10. [Infrastructure and Deployment](#10-infrastructure-and-deployment)
11. [Security and Best Practices](#11-security-and-best-practices)
12. [Data Lineage and Quality](#12-data-lineage-and-quality)
13. [Testing and Validation](#13-testing-and-validation)
14. [Results and Insights](#14-results-and-insights)
15. [Future Enhancements](#15-future-enhancements)
16. [References](#16-references)
17. [Appendices](#17-appendices)

---

## 1. Executive Summary

### 1.1 Project Overview

The Transit Service Reliability & Demand Planning System is a production-capable prototype designed to help metropolitan transit operators monitor, analyze, and forecast transit service performance. The system integrates real-time streaming data, historical schedule data, and machine learning models to provide actionable insights for transit operations.

### 1.2 Key Objectives

1. **Real-Time Monitoring**: Provide live tracking of transit departures with delay information
2. **Historical Analysis**: Analyze GTFS schedule data to understand service patterns
3. **Demand Forecasting**: Use machine learning to predict future transit demand
4. **Natural Language Querying**: Enable users to query data using natural language
5. **Interactive Visualization**: Present data through intuitive dashboards and maps

### 1.3 System Capabilities

- **Data Ingestion**: Automated ingestion of GTFS feeds and real-time Transit API data
- **Data Transformation**: Multi-stage ETL pipeline using dbt
- **Machine Learning**: Time-series forecasting using Snowflake ML
- **Real-Time Processing**: Kafka-based streaming pipeline
- **API Services**: RESTful API with LLM integration
- **Web Dashboard**: Interactive React-based frontend

### 1.4 Technologies Used

- **Orchestration**: Apache Airflow
- **Streaming**: Apache Kafka
- **Transformation**: dbt (data build tool)
- **Data Warehouse**: Snowflake
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Vite
- **ML**: Snowflake ML FORECAST
- **LLM**: Perplexity AI
- **Secrets Management**: AWS Secrets Manager

---

## 2. Introduction

### 2.1 Problem Statement

Transit operators face challenges in:
- Monitoring real-time service performance
- Understanding historical service patterns
- Predicting future demand
- Making data-driven decisions
- Providing transparent information to riders

### 2.2 Solution Approach

This system addresses these challenges by:
1. Integrating multiple data sources (GTFS, Transit API)
2. Processing data through a scalable pipeline
3. Applying machine learning for predictions
4. Providing intuitive interfaces for analysis
5. Enabling natural language data queries

### 2.3 Scope

**In Scope**:
- GTFS data ingestion (BART, VTA)
- Real-time streaming data processing
- Data transformation and analytics
- ML-based demand forecasting
- Web-based dashboard
- Natural language query interface

**Out of Scope** (Future Work):
- Mobile application
- Real-time alerts and notifications
- Multi-tenant support
- Advanced ML models (delay prediction with full data)
- Integration with other transit systems

---

## 3. System Architecture

### 3.1 High-Level Architecture

The system follows a layered architecture pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  React Frontend (Dashboard, Analytics, Maps, Forecasts)    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      API Layer                               │
│  FastAPI Backend + Perplexity LLM Integration               │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                  Data Processing Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Airflow    │  │     dbt      │  │  Snowflake   │      │
│  │ Orchestration│  │Transformation│  │     ML       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Data Ingestion Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  GTFS Feeds  │  │ Transit API  │  │    Kafka     │     │
│  │   (BART,     │  │  (Real-time)  │  │  Streaming   │     │
│  │    VTA)      │  │               │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

**Figure 3.1: System Architecture Overview**

*[Screenshot Placeholder: Complete system architecture diagram showing all components and their connections]*

### 3.2 Component Architecture

#### 3.2.1 Data Ingestion Components

**GTFS Ingestion**:
- **Component**: `gtfs_incremental_ingestion` DAG
- **Frequency**: Every 6 hours
- **Source**: GTFS feeds from BART and VTA
- **Destination**: Snowflake `LANDING` schema
- **Script**: `ingestion/fetch_gtfs_incremental.py`

**Streaming Ingestion**:
- **Component**: `transit_streaming` DAG
- **Frequency**: Hourly
- **Source**: Transit API (real-time departures)
- **Pipeline**: Producer → Kafka → Consumer → Snowflake
- **Scripts**: 
  - `ingestion/kafka_streaming_producer.py`
  - `ingestion/kafka_consumer_to_landing.py`

*[Screenshot Placeholder: Airflow DAG graph showing all three DAGs and their dependencies]*

#### 3.2.2 Data Transformation Components

**dbt Models**:
- **Landing to Raw**: Clean and standardize GTFS data
- **Streaming to Analytics**: Process real-time data
- **Transform**: Business logic and enrichment
- **Analytics**: Final metrics and KPIs

**Schema Progression**:
```
LANDING → ANALYTICS_RAW → ANALYTICS_TRANSFORM → ANALYTICS_ANALYTICS
```

*[Screenshot Placeholder: dbt lineage diagram showing all models and their dependencies]*

#### 3.2.3 Machine Learning Components

**ML Pipeline**:
- **DAG**: `ml_forecast_dag`
- **Frequency**: Every 6 hours
- **Models**: 
  - Demand Forecast Model
  - Delay Forecast Model (when data available)
- **Technology**: Snowflake ML FORECAST
- **Output**: `ANALYTICS_ML.DEMAND_FORECAST`

*[Screenshot Placeholder: ML model training process in Snowflake]*

### 3.3 Data Flow Diagrams

#### 3.3.1 GTFS Data Flow

```
GTFS Feed (BART/VTA)
    ↓
[Airflow: gtfs_incremental_dag]
    ↓
fetch_gtfs_incremental.py
    ↓
Parse GTFS Files (stops.txt, routes.txt, trips.txt, stop_times.txt)
    ↓
Snowflake LANDING.LANDING_GTFS_* tables
    ↓
[dbt: landing_to_raw models]
    ↓
ANALYTICS_RAW.STG_GTFS_* tables
    ↓
[dbt: transform/route_departures.sql]
    ↓
ANALYTICS_TRANSFORM.ROUTE_DEPARTURES
    ↓
[dbt: analytics/route_performance.sql]
    ↓
ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE
```

**Figure 3.2: GTFS Data Flow**

*[Screenshot Placeholder: Detailed GTFS data flow diagram with table names and transformations]*

#### 3.3.2 Streaming Data Flow

```
Transit API (Real-time Departures)
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
[dbt: streaming_to_analytics/stg_streaming_departures.sql]
    ↓
ANALYTICS_RAW.STG_STREAMING_DEPARTURES
    ↓
[Used in analytics models for real-time metrics]
```

**Figure 3.3: Streaming Data Flow**

*[Screenshot Placeholder: Kafka streaming pipeline diagram showing producer, topic, and consumer]*

#### 3.3.3 ML Forecasting Flow

```
ANALYTICS_TRANSFORM.ROUTE_DEPARTURES
    ↓
[Airflow: ml_forecast_dag]
    ↓
Create Training Data View (90 days historical)
    ↓
CREATE SNOWFLAKE.ML.FORECAST DEMAND_FORECAST_MODEL
    ↓
Train Model on Historical Data
    ↓
CALL DEMAND_FORECAST_MODEL!FORECAST(FORECASTING_PERIODS => 7)
    ↓
ANALYTICS_ML.DEMAND_FORECAST
    ↓
[API: /api/forecasts/demand]
    ↓
[Frontend: Forecasts Page]
```

**Figure 3.4: ML Forecasting Flow**

*[Screenshot Placeholder: ML model creation and forecast generation process]*

### 3.4 System Integration Points

1. **Airflow ↔ Snowflake**: Direct connection for data loading
2. **Kafka ↔ Snowflake**: Consumer writes to landing tables
3. **dbt ↔ Snowflake**: Transformation queries
4. **FastAPI ↔ Snowflake**: Data retrieval for API
5. **FastAPI ↔ Perplexity**: LLM query processing
6. **Frontend ↔ FastAPI**: REST API calls
7. **Airflow ↔ AWS Secrets Manager**: Credential retrieval

*[Screenshot Placeholder: Integration diagram showing all connection points]*

---

## 4. Technology Stack

### 4.1 Backend Technologies

#### 4.1.1 Python 3.9+

**Purpose**: Primary programming language for backend services

**Usage**:
- Airflow DAGs
- Data ingestion scripts
- FastAPI backend
- dbt Python models (if needed)

**Key Libraries**:
- `fastapi`: Web framework
- `snowflake-connector-python`: Snowflake connectivity
- `kafka-python`: Kafka producer/consumer
- `boto3`: AWS SDK for Secrets Manager
- `pydantic`: Data validation

#### 4.1.2 Apache Airflow 2.x

**Purpose**: Workflow orchestration and scheduling

**Configuration**:
- **Executor**: LocalExecutor
- **Database**: PostgreSQL (metadata)
- **Deployment**: Docker containers
- **Web UI**: Port 8080

**DAGs**:
1. `gtfs_incremental_ingestion`: GTFS data loading
2. `transit_streaming`: Kafka streaming pipeline
3. `ml_forecast_dag`: ML model training and forecasting

**Features Used**:
- Task dependencies
- Retry logic
- Logging
- Variable management
- Connection management

*[Screenshot Placeholder: Airflow UI showing all DAGs and their status]*

#### 4.1.3 Apache Kafka

**Purpose**: Real-time data streaming

**Components**:
- **Zookeeper**: Coordination service
- **Kafka Broker**: Message broker
- **Producer**: Fetches Transit API data
- **Consumer**: Writes to Snowflake

**Configuration**:
- **Bootstrap Servers**: `localhost:9092`
- **Topic**: `transit-streaming`
- **Consumer Group**: `transit-consumers`
- **Partitions**: 1 (development)

**Deployment**: Docker Compose

*[Screenshot Placeholder: Kafka topic monitoring showing message throughput]*

#### 4.1.4 dbt (data build tool) 1.x

**Purpose**: Data transformation and modeling

**Project Structure**:
```
dbt/transit_dbt/
├── models/
│   ├── landing_to_raw/          # GTFS staging
│   ├── streaming_to_analytics/  # Streaming staging
│   ├── transform/               # Business logic
│   ├── analytics/               # Final metrics
│   └── ml_forecasts/            # ML inputs
├── dbt_project.yml
└── profiles.yml
```

**Materialization Strategies**:
- **Table**: Large, frequently queried data
- **View**: Lightweight transformations
- **Incremental**: Append-only data with merge strategy

**Schemas**:
- `ANALYTICS_RAW`: Cleaned raw data
- `ANALYTICS_TRANSFORM`: Business transformations
- `ANALYTICS_ANALYTICS`: Final analytics
- `ANALYTICS_ML`: ML training data

*[Screenshot Placeholder: dbt docs showing model lineage and dependencies]*

#### 4.1.5 Snowflake

**Purpose**: Cloud data warehouse

**Configuration**:
- **Database**: `USER_DB_HORNET`
- **Warehouse**: `HORNET_QUERY_WH`
- **Role**: `TRAINING_ROLE`
- **Region**: US-West-2

**Schemas**:
1. `LANDING`: Raw ingested data
2. `ANALYTICS_RAW`: Cleaned staging data
3. `ANALYTICS_TRANSFORM`: Transformed data
4. `ANALYTICS_ANALYTICS`: Final analytics
5. `ANALYTICS_ML`: ML models and forecasts

**Key Features Used**:
- Time Travel
- Cloning
- Snowflake ML FORECAST
- Views
- Tables
- Stored Procedures (via Python)

*[Screenshot Placeholder: Snowflake worksheet showing table structure and sample data]*

#### 4.1.6 FastAPI

**Purpose**: REST API framework

**Features**:
- Automatic OpenAPI documentation
- Async support
- Request validation
- CORS middleware
- Dependency injection

**Endpoints**: See Section 8.2

*[Screenshot Placeholder: FastAPI Swagger UI showing all endpoints]*

#### 4.1.7 Perplexity AI

**Purpose**: LLM for natural language queries

**Integration**:
- API key stored in AWS Secrets Manager
- Schema context provided to LLM
- SQL generation from natural language
- Response formatting

**Usage**: `/api/chat` endpoint

*[Screenshot Placeholder: Perplexity API integration showing query flow]*

### 4.2 Frontend Technologies

#### 4.2.1 React 18.2.0

**Purpose**: UI framework

**Features Used**:
- Functional components with hooks
- Context API for state management
- React Router for navigation
- Component composition

#### 4.2.2 TypeScript

**Purpose**: Type-safe JavaScript

**Benefits**:
- Compile-time error checking
- Better IDE support
- Self-documenting code
- Refactoring safety

#### 4.2.3 Vite

**Purpose**: Build tool and dev server

**Features**:
- Fast HMR (Hot Module Replacement)
- Optimized production builds
- Plugin ecosystem

#### 4.2.4 Tailwind CSS

**Purpose**: Utility-first CSS framework

**Usage**: Styling all components

#### 4.2.5 Recharts

**Purpose**: Chart library

**Charts Used**:
- Line charts (time series)
- Bar charts (distributions)
- Area charts (trends)

#### 4.2.6 React Leaflet

**Purpose**: Map visualization

**Features**:
- Interactive maps
- Marker clustering
- Route visualization
- Stop locations

### 4.3 Infrastructure Technologies

#### 4.3.1 Docker

**Purpose**: Containerization

**Containers**:
- Airflow (webserver, scheduler, init)
- PostgreSQL (Airflow metadata)
- Kafka
- Zookeeper

#### 4.3.2 Docker Compose

**Purpose**: Multi-container orchestration

**Configuration**: `docker-compose.local.yml`

#### 4.3.3 AWS Secrets Manager

**Purpose**: Secure credential storage

**Secrets**:
- `transit/snowflake-dev`: Snowflake credentials
- `transit/perplexity`: Perplexity API key

**Access**: Via AWS CLI profile `transit-system`

*[Screenshot Placeholder: AWS Secrets Manager console showing stored secrets]*

---

## 5. Data Sources and Ingestion

### 5.1 GTFS Data

#### 5.1.1 Data Source

**Format**: General Transit Feed Specification (GTFS)

**Agencies**:
- **BART**: Bay Area Rapid Transit
- **VTA**: Santa Clara Valley Transportation Authority

**Files Ingested**:
- `stops.txt`: Stop locations and names
- `routes.txt`: Route definitions
- `trips.txt`: Trip schedules
- `stop_times.txt`: Arrival/departure times

**Update Frequency**: Every 6 hours (via Airflow)

#### 5.1.2 Ingestion Process

**DAG**: `gtfs_incremental_ingestion`

**Steps**:
1. Fetch GTFS feeds from agency URLs
2. Parse GTFS files
3. Load to Snowflake `LANDING` schema
4. Track load history in `GTFS_LOAD_HISTORY` table

**Script**: `ingestion/fetch_gtfs_incremental.py`

**Incremental Logic**:
- First run: Load from `initial_load_date` (2025-08-01)
- Subsequent runs: Only new/updated data

*[Screenshot Placeholder: GTFS ingestion DAG in Airflow showing task execution]*

#### 5.1.3 Landing Tables

**Schema**: `LANDING`

**Tables**:
- `LANDING_GTFS_STOPS`
- `LANDING_GTFS_ROUTES`
- `LANDING_GTFS_TRIPS`
- `LANDING_GTFS_STOP_TIMES`
- `GTFS_LOAD_HISTORY`

**Table Structure**: See `TABLES_REFERENCE.md`

*[Screenshot Placeholder: Snowflake showing GTFS landing tables with sample data]*

### 5.2 Real-Time Streaming Data

#### 5.2.1 Data Source

**API**: Transit API (transit.land)

**Data Type**: Real-time departure information

**Fields**:
- Stop information
- Route information
- Scheduled vs. actual departure times
- Delay information
- Real-time status flags

**Update Frequency**: Every 5 minutes (via Kafka producer)

#### 5.2.2 Streaming Pipeline

**DAG**: `transit_streaming`

**Components**:

1. **Producer** (`kafka_streaming_producer.py`):
   - Polls Transit API every 5 minutes
   - Fetches departures for configured agencies
   - Sends messages to Kafka topic `transit-streaming`
   - Rate limiting: 5 calls per minute

2. **Kafka Topic**:
   - Topic: `transit-streaming`
   - Format: JSON messages
   - Retention: 7 days

3. **Consumer** (`kafka_consumer_to_landing.py`):
   - Reads from Kafka topic
   - Transforms messages
   - Inserts to `LANDING.LANDING_STREAMING_DEPARTURES`
   - Commits offsets

**Flow**:
```
Transit API → Producer → Kafka → Consumer → Snowflake
```

*[Screenshot Placeholder: Kafka streaming pipeline showing producer and consumer metrics]*

#### 5.2.3 Landing Table

**Table**: `LANDING.LANDING_STREAMING_DEPARTURES`

**Key Columns**:
- `ID`: Unique departure identifier
- `GLOBAL_STOP_ID`: Stop identifier
- `GLOBAL_ROUTE_ID`: Route identifier
- `SCHEDULED_DEPARTURE_TIME`: Scheduled time
- `DEPARTURE_TIME`: Actual/predicted time
- `DELAY_SECONDS`: Delay in seconds
- `IS_REAL_TIME`: Real-time flag
- `CONSUMED_AT`: Timestamp when consumed

*[Screenshot Placeholder: Streaming departures table with real-time data]*

### 5.3 Data Quality Considerations

#### 5.3.1 GTFS Data Quality

**Validation**:
- Required fields present
- Data type validation
- Referential integrity (routes → trips → stop_times)
- Date range validation

**Error Handling**:
- Logging of invalid records
- Skip invalid records, continue processing
- Alert on high error rates

#### 5.3.2 Streaming Data Quality

**Validation**:
- JSON schema validation
- Required fields check
- Timestamp validation
- Agency code validation

**Error Handling**:
- Dead letter queue for failed messages
- Retry logic for transient failures
- Monitoring of consumer lag

---

## 6. Data Transformation Pipeline

### 6.1 dbt Project Structure

**Location**: `dbt/transit_dbt/`

**Organization**:
```
models/
├── landing_to_raw/          # Stage 1: Clean raw data
├── streaming_to_analytics/  # Stage 1: Clean streaming data
├── transform/               # Stage 2: Business logic
├── analytics/               # Stage 3: Final metrics
└── ml_forecasts/            # ML training data
```

### 6.2 Transformation Stages

#### 6.2.1 Stage 1: Landing to Raw

**Purpose**: Clean and standardize raw data

**Models**:
- `stg_gtfs_stops.sql`
- `stg_gtfs_routes.sql`
- `stg_gtfs_trips.sql`
- `stg_gtfs_stop_times.sql`
- `stg_streaming_departures.sql`

**Transformations**:
- Column name standardization
- Data type conversion
- Null handling
- Agency code normalization

**Output Schema**: `ANALYTICS_RAW`

*[Screenshot Placeholder: dbt model showing landing_to_raw transformations]*

#### 6.2.2 Stage 2: Transform

**Purpose**: Business logic and enrichment

**Models**:
- `route_departures.sql`

**Transformations**:
- Join GTFS data (routes, trips, stops, stop_times)
- Calculate derived fields
- Aggregate to route-stop level
- Add service date information

**Output Schema**: `ANALYTICS_TRANSFORM`

*[Screenshot Placeholder: Transform model showing business logic]*

#### 6.2.3 Stage 3: Analytics

**Purpose**: Final metrics and KPIs

**Models**:
- `route_performance.sql`

**Metrics Calculated**:
- Total trips per route
- Total stops per route
- Total departures
- Streaming departures count
- Average delay seconds
- On-time performance percentage

**Output Schema**: `ANALYTICS_ANALYTICS`

*[Screenshot Placeholder: Analytics model showing final metrics]*

### 6.3 Materialization Strategies

#### 6.3.1 Table Materialization

**Used For**:
- Large datasets
- Frequently queried data
- Incremental updates

**Examples**:
- `stg_gtfs_*` models
- `route_departures`
- `route_performance`

#### 6.3.2 View Materialization

**Used For**:
- Lightweight transformations
- Infrequently queried data
- No storage cost

**Examples**:
- Staging views (if applicable)

#### 6.3.3 Incremental Materialization

**Used For**:
- Append-only data
- Large historical datasets
- Merge strategies

**Configuration**:
```yaml
+materialized: incremental
+unique_key: id
+incremental_strategy: merge
```

### 6.4 Data Lineage

**dbt Lineage**:
```
LANDING.LANDING_GTFS_STOPS
    ↓
ANALYTICS_RAW.STG_GTFS_STOPS
    ↓
ANALYTICS_TRANSFORM.ROUTE_DEPARTURES
    ↓
ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE
```

*[Screenshot Placeholder: Complete dbt lineage diagram showing all dependencies]*

### 6.5 Testing

**dbt Tests**:
- Not null tests
- Unique tests
- Referential integrity tests
- Accepted values tests

**Run Tests**:
```bash
dbt test --target snowflake
```

---

## 7. Machine Learning Pipeline

### 7.1 ML Architecture

**Technology**: Snowflake ML FORECAST

**Purpose**: Time-series forecasting for transit demand

**Models**:
1. **Demand Forecast Model**: Predicts future departures by route
2. **Delay Forecast Model**: Predicts delays (when sufficient data available)

### 7.2 Demand Forecasting

#### 7.2.1 Training Data Preparation

**Source**: `ANALYTICS_TRANSFORM.ROUTE_DEPARTURES`

**View**: `ANALYTICS_ML.VW_DEMAND_TRAINING_DATA`

**Data Structure**:
- `SERIES`: Route ID (time series identifier)
- `DATE`: Date (timestamp)
- `DEPARTURE_COUNT`: Target variable (daily departures)

**Historical Window**: 90 days

**Aggregation**: Daily departures per route

*[Screenshot Placeholder: Training data view showing time series structure]*

#### 7.2.2 Model Creation

**DAG**: `ml_forecast_dag`

**Process**:
1. Create training data view
2. Create Snowflake ML FORECAST model:
   ```sql
   CREATE OR REPLACE SNOWFLAKE.ML.FORECAST DEMAND_FORECAST_MODEL(
       INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'VW_DEMAND_TRAINING_DATA'),
       SERIES_COLNAME => 'SERIES',
       TIMESTAMP_COLNAME => 'DATE',
       TARGET_COLNAME => 'DEPARTURE_COUNT',
       CONFIG_OBJECT => { 'ON_ERROR': 'SKIP' }
   )
   ```
3. Model automatically trains on historical data
4. Generate forecasts for next 7 days

*[Screenshot Placeholder: ML model creation in Snowflake]*

#### 7.2.3 Forecast Generation

**Method**: `CALL DEMAND_FORECAST_MODEL!FORECAST(FORECASTING_PERIODS => 7)`

**Output**: Forecasts with prediction intervals

**Storage**: `ANALYTICS_ML.DEMAND_FORECAST`

**Columns**:
- `ROUTE_ID`: Route identifier
- `ROUTE_SHORT_NAME`: Route name
- `AGENCY`: Agency code
- `FORECAST_DATE`: Forecast date
- `PREDICTED_DEPARTURES`: Predicted count
- `FORECAST_GENERATED_AT`: Timestamp

*[Screenshot Placeholder: Forecast results in Snowflake table]*

### 7.3 Delay Forecasting

**Status**: Implemented but requires sufficient streaming data

**Process**: Similar to demand forecasting but uses delay data from streaming departures

**Training Data**: `ANALYTICS_RAW.STG_STREAMING_DEPARTURES`

**Model**: `DELAY_FORECAST_MODEL`

**Output**: `ANALYTICS_ML.DELAY_FORECAST`

### 7.4 Model Refresh

**Frequency**: Every 6 hours (via Airflow)

**Process**:
1. Drop existing model
2. Recreate with latest data
3. Retrain
4. Generate new forecasts
5. Update forecast table

*[Screenshot Placeholder: ML DAG execution showing model refresh]*

---

## 8. API and Backend Services

### 8.1 FastAPI Application

**Location**: `api/main.py`

**Framework**: FastAPI

**Features**:
- Automatic OpenAPI documentation
- Request validation
- CORS middleware
- Async support
- Error handling

### 8.2 API Endpoints

#### 8.2.1 Health Check

**Endpoint**: `GET /api/health`

**Purpose**: Service health check

**Response**:
```json
{
  "status": "healthy",
  "service": "transit-ops-api"
}
```

#### 8.2.2 KPIs

**Endpoint**: `GET /api/kpis?agency={agency}`

**Purpose**: Key performance indicators

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

#### 8.2.3 Routes

**Endpoint**: `GET /api/routes?agency={agency}`

**Purpose**: Route information

**Response**: List of routes with details

#### 8.2.4 Live Data

**Endpoint**: `GET /api/live-data?agency={agency}`

**Purpose**: Real-time departure data

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
      "avg_delay": -99.0,
      "on_time_count": 457,
      "on_time_pct": 45.7
    }
  }
}
```

#### 8.2.5 Forecasts

**Endpoint**: `GET /api/forecasts/demand?hours={hours}&agency={agency}`

**Purpose**: ML demand forecasts

**Response**: Forecast data for specified time horizon

#### 8.2.6 Chat (LLM)

**Endpoint**: `POST /api/chat`

**Purpose**: Natural language queries

**Request**:
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

#### 8.2.7 Admin Status

**Endpoint**: `GET /api/admin/status`

**Purpose**: System status and table information

**Response**: Comprehensive system status

*[Screenshot Placeholder: FastAPI Swagger UI showing all endpoints]*

### 8.3 LLM Integration

#### 8.3.1 Perplexity AI Integration

**Location**: `api/llm/chat_handler.py`

**Components**:
- `PerplexityClient`: API client
- `ChatHandler`: Main logic
- `SchemaContext`: Snowflake schema information

**Process**:
1. User sends natural language question
2. System determines if data query needed
3. Generate SQL query using LLM with schema context
4. Execute query against Snowflake
5. Format response for user

**Schema Context**: Includes table definitions, column descriptions, sample queries

*[Screenshot Placeholder: LLM query flow showing SQL generation]*

### 8.4 Connection Management

**Location**: `api/warehouse_connection.py`

**Function**: `get_warehouse_connection()`

**Features**:
- Connection pooling
- Automatic retry
- Error handling
- Context manager support

**Configuration**: Loaded from `config.yaml` and AWS Secrets Manager

---

## 9. Frontend Application

### 9.1 Application Structure

**Framework**: React 18 with TypeScript

**Build Tool**: Vite

**Location**: `ui/src/`

**Structure**:
```
src/
├── components/      # Reusable components
├── pages/          # Page components
├── services/       # API services
├── types/          # TypeScript types
└── utils/          # Utility functions
```

### 9.2 Pages

#### 9.2.1 Dashboard (`/`)

**Purpose**: Overview and KPIs

**Components**:
- KPI cards (Total Today, Real-time, Streaming, Avg Delay)
- Quick stats
- System status

*[Screenshot Placeholder: Dashboard page showing KPIs and overview]*

#### 9.2.2 Routes (`/routes`)

**Purpose**: Route information and performance

**Features**:
- Route listing
- Filter by agency
- Route details
- Performance metrics

*[Screenshot Placeholder: Routes page showing route list and details]*

#### 9.2.3 Analytics (`/analytics`)

**Purpose**: Historical analysis

**Features**:
- Time-series charts
- Performance trends
- Comparative analysis
- Agency filtering

*[Screenshot Placeholder: Analytics page with charts and trends]*

#### 9.2.4 Map View (`/map`)

**Purpose**: Geographic visualization

**Features**:
- Interactive map (Leaflet)
- Stop locations
- Route visualization
- Real-time markers

*[Screenshot Placeholder: Map view showing stops and routes]*

#### 9.2.5 Forecasts (`/forecasts`)

**Purpose**: ML predictions

**Features**:
- Demand forecast charts
- Time horizon selection (6h, 24h, 7d)
- Agency filtering
- Forecast vs. actual comparison

*[Screenshot Placeholder: Forecasts page showing ML predictions]*

#### 9.2.6 Live Data (`/live-data`)

**Purpose**: Real-time departures

**Features**:
- Departure table
- Delay severity distribution chart
- Departures by hour chart
- Data freshness indicators
- Auto-refresh (30 seconds)

*[Screenshot Placeholder: Live Data page with real-time departures]*

#### 9.2.7 Data Query (`/query`)

**Purpose**: Natural language queries

**Features**:
- Chat interface
- LLM-powered queries
- Query history
- Response formatting

*[Screenshot Placeholder: Data Query page with chat interface]*

#### 9.2.8 BI Dashboard (`/bi-dashboard`)

**Purpose**: Business intelligence views

**Features**:
- Preset dashboards
- Export capabilities
- Custom visualizations

*[Screenshot Placeholder: BI Dashboard with preset views]*

#### 9.2.9 Admin (`/admin`)

**Purpose**: System administration

**Features**:
- System status
- Table information
- Data quality metrics
- Pipeline health

*[Screenshot Placeholder: Admin page showing system status]*

### 9.3 State Management

**Approach**: React Context API

**Context**: `TransportContext`

**State**:
- Agency filter
- Data refresh intervals
- Loading states

### 9.4 API Integration

**Service**: `api/transitApi.ts`

**Base URL**: `http://localhost:8000/api`

**Features**:
- Error handling
- Request/response interceptors
- Type-safe API calls

### 9.5 Styling

**Framework**: Tailwind CSS

**Approach**: Utility-first CSS

**Theme**: Dark mode with transit-themed colors

---

## 10. Infrastructure and Deployment

### 10.1 Local Development Environment

#### 10.1.1 Docker Compose Setup

**File**: `docker-compose.local.yml`

**Services**:
- **Zookeeper**: Kafka coordination
- **Kafka**: Message broker
- **PostgreSQL**: Airflow metadata
- **Airflow Webserver**: Web UI
- **Airflow Scheduler**: Task scheduler
- **Airflow Init**: Initialization

**Start Command**:
```bash
./start_local.sh
```

*[Screenshot Placeholder: Docker Compose services running]*

#### 10.1.2 Backend Setup

**Requirements**:
- Python 3.9+
- Virtual environment
- Dependencies from `api/requirements.txt`

**Start Command**:
```bash
cd api
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 10.1.3 Frontend Setup

**Requirements**:
- Node.js 18+
- npm

**Start Command**:
```bash
cd ui
npm install
npm run dev
```

### 10.2 Master Start Script

**File**: `start_all.sh`

**Purpose**: Start all services with one command

**Process**:
1. Check Docker status
2. Start Docker services (Kafka, Airflow)
3. Start Backend API
4. Start Frontend

**Usage**:
```bash
./start_all.sh
```

*[Screenshot Placeholder: Master start script execution]*

### 10.3 AWS Integration

#### 10.3.1 AWS Secrets Manager

**Purpose**: Secure credential storage

**Secrets**:
- `transit/snowflake-dev`: Snowflake credentials
- `transit/perplexity`: Perplexity API key

**Access**: Via AWS CLI profile `transit-system`

**Region**: `us-west-2`

*[Screenshot Placeholder: AWS Secrets Manager console]*

#### 10.3.2 AWS CLI Configuration

**Profile**: `transit-system`

**Configuration**:
```bash
aws configure --profile transit-system
```

### 10.4 Snowflake Configuration

**Database**: `USER_DB_HORNET`

**Warehouse**: `HORNET_QUERY_WH`

**Role**: `TRAINING_ROLE`

**Schemas**: See Section 3.2.3

*[Screenshot Placeholder: Snowflake account and warehouse configuration]*

---

## 11. Security and Best Practices

### 11.1 Security Measures

#### 11.1.1 Credential Management

**Approach**: AWS Secrets Manager

**Benefits**:
- No hardcoded credentials
- Centralized management
- Audit trail
- Rotation support

**Implementation**: All credentials loaded at runtime

*[Screenshot Placeholder: Secrets Manager showing secret configuration]*

#### 11.1.2 Data Access Control

**Snowflake Roles**: Role-based access control

**Principle**: Least privilege access

**Connection**: Uses dedicated role for application

#### 11.1.3 API Security

**CORS**: Configured for specific origins

**Validation**: Request validation via Pydantic

**Error Handling**: No sensitive information in error messages

### 11.2 Best Practices

#### 11.2.1 Code Organization

- Modular design
- Separation of concerns
- Clear naming conventions
- Documentation

#### 11.2.2 Data Quality

- Validation at ingestion
- dbt tests
- Error logging
- Monitoring

#### 11.2.3 Performance

- Query optimization
- Connection pooling
- Caching where appropriate
- Incremental processing

#### 11.2.4 Monitoring

- Logging at all levels
- Error tracking
- Performance metrics
- Health checks

---

## 12. Data Lineage and Quality

### 12.1 Data Lineage

**Complete Flow**:
```
GTFS Feeds → LANDING → ANALYTICS_RAW → ANALYTICS_TRANSFORM → ANALYTICS_ANALYTICS
Transit API → Kafka → LANDING → ANALYTICS_RAW → Analytics Models
Analytics Data → ML Training → ML Models → Forecasts
```

*[Screenshot Placeholder: Complete data lineage diagram]*

### 12.2 Data Quality Measures

#### 12.2.1 Validation

- Schema validation
- Data type checks
- Required field validation
- Referential integrity

#### 12.2.2 Monitoring

- Data freshness metrics
- Record counts
- Error rates
- Quality scores

#### 12.2.3 dbt Tests

- Not null tests
- Unique tests
- Relationship tests
- Accepted values

*[Screenshot Placeholder: dbt test results]*

---

## 13. Testing and Validation

### 13.1 Data Pipeline Testing

#### 13.1.1 Ingestion Tests

- GTFS file parsing
- Data loading to Snowflake
- Incremental logic
- Error handling

#### 13.1.2 Transformation Tests

- dbt model execution
- Data quality checks
- Transformation logic
- Incremental updates

#### 13.1.3 ML Model Tests

- Model creation
- Training data quality
- Forecast generation
- Result validation

### 13.2 API Testing

**Endpoints Tested**:
- Health check
- KPI endpoints
- Live data endpoints
- Forecast endpoints
- Chat endpoint

**Tools**: Manual testing + Postman/curl

*[Screenshot Placeholder: API test results]*

### 13.3 Frontend Testing

**Testing**:
- Component rendering
- API integration
- User interactions
- Error handling

### 13.4 Integration Testing

**Scenarios**:
- End-to-end data flow
- API to frontend integration
- LLM query flow
- Real-time data updates

---

## 14. Results and Insights

### 14.1 Data Insights

#### 14.1.1 Route Performance

**Metrics**:
- On-time performance by route
- Average delays
- Total departures
- Peak hours

**Findings**: [To be populated with actual insights from data]

*[Screenshot Placeholder: Route performance dashboard]*

#### 14.1.2 Demand Patterns

**Metrics**:
- Hourly demand patterns
- Peak periods
- Route popularity
- Seasonal trends

**Findings**: [To be populated with actual insights from data]

*[Screenshot Placeholder: Demand patterns visualization]*

#### 14.1.3 Reliability Metrics

**Metrics**:
- Overall on-time performance
- Delay distribution
- Real-time data coverage
- Service reliability scores

**Findings**: [To be populated with actual insights from data]

*[Screenshot Placeholder: Reliability metrics dashboard]*

### 14.2 ML Forecast Accuracy

**Evaluation**: [To be populated with forecast accuracy metrics]

**Use Cases**:
- Demand planning
- Resource allocation
- Service adjustments

*[Screenshot Placeholder: Forecast accuracy metrics]*

### 14.3 System Performance

**Metrics**:
- API response times
- Data freshness
- Pipeline execution times
- Frontend load times

**Findings**: [To be populated with performance metrics]

---

## 15. Future Enhancements

### 15.1 Short-Term Enhancements

1. **Delay Forecasting**: Complete implementation when sufficient streaming data available
2. **Alert System**: Real-time alerts for delays and service disruptions
3. **Mobile App**: Native mobile application
4. **Advanced Analytics**: More sophisticated analytics models

### 15.2 Long-Term Enhancements

1. **Multi-Tenant Support**: Support for multiple transit agencies
2. **Advanced ML Models**: Deep learning models for predictions
3. **Real-Time Recommendations**: AI-powered service recommendations
4. **Integration**: Integration with other transit systems
5. **Scalability**: Cloud-native deployment (AWS ECS, Kubernetes)

### 15.3 Research Opportunities

1. **Predictive Maintenance**: Predict vehicle maintenance needs
2. **Optimization**: Route and schedule optimization
3. **Demand-Responsive Transit**: Dynamic routing based on demand
4. **Sustainability Metrics**: Carbon footprint and environmental impact

---

## 16. References

### 16.1 Technical Documentation

1. Apache Airflow Documentation: https://airflow.apache.org/docs/
2. dbt Documentation: https://docs.getdbt.com/
3. Snowflake Documentation: https://docs.snowflake.com/
4. FastAPI Documentation: https://fastapi.tiangolo.com/
5. React Documentation: https://react.dev/
6. Kafka Documentation: https://kafka.apache.org/documentation/

### 16.2 Data Sources

1. GTFS Specification: https://gtfs.org/
2. Transit API: https://transit.land/
3. BART GTFS: [BART GTFS Feed URL]
4. VTA GTFS: [VTA GTFS Feed URL]

### 16.3 Academic References

1. Time-Series Forecasting: [Relevant papers]
2. Transit Analytics: [Relevant papers]
3. Machine Learning in Transportation: [Relevant papers]

### 16.4 Tools and Libraries

1. Perplexity AI: https://www.perplexity.ai/
2. AWS Secrets Manager: https://aws.amazon.com/secrets-manager/
3. Recharts: https://recharts.org/
4. React Leaflet: https://react-leaflet.js.org/

---

## 17. Appendices

### 17.1 Appendix A: Table Definitions

See `TABLES_REFERENCE.md` for complete table documentation.

*[Screenshot Placeholder: Complete table reference document]*

### 17.2 Appendix B: ER Diagram

Entity-Relationship diagram showing all tables and relationships.

*[Screenshot Placeholder: ER diagram showing all entities and relationships]*

### 17.3 Appendix C: API Endpoint Reference

Complete API endpoint documentation.

*[Screenshot Placeholder: Complete API documentation]*

### 17.4 Appendix D: Configuration Files

Sample configuration files with explanations.

*[Screenshot Placeholder: Configuration file examples]*

### 17.5 Appendix E: Deployment Guide

Step-by-step deployment instructions.

*[Screenshot Placeholder: Deployment guide]*

### 17.6 Appendix F: Troubleshooting Guide

Common issues and solutions.

*[Screenshot Placeholder: Troubleshooting guide]*

### 17.7 Appendix G: Team Contributions

Individual team member contributions.

**Team Members**:
- Ayush Gawai: [Contributions]
- Khushi Donda: [Contributions]
- Aryan Choudhari: [Contributions]
- Bhoomika Lnu: [Contributions]

### 17.8 Appendix H: Screenshots Index

Complete index of all screenshots referenced in this document.

1. System Architecture Diagram
2. Airflow DAG Graph
3. dbt Lineage Diagram
4. Data Flow Diagrams
5. ML Model Training
6. FastAPI Swagger UI
7. Frontend Dashboard Pages
8. Admin Panel
9. AWS Secrets Manager
10. Snowflake Tables
11. And more...

---

## Document Information

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Authors**: Group 9 (Ayush Gawai, Khushi Donda, Aryan Choudhari, Bhoomika Lnu)  
**Format**: IEEE Technical Documentation Format  
**Status**: Final

---

**End of Document**

