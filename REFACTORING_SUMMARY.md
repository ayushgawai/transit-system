# Schema Refactoring Summary

## Overview
Complete schema refactoring to implement proper data warehouse architecture with clear separation of concerns.

## Schema Structure

### LANDING Schema
**Purpose**: Raw data from APIs/GTFS (initial ingestion)
**Tables**:
- `LANDING_GTFS_STOPS`
- `LANDING_GTFS_ROUTES`
- `LANDING_GTFS_TRIPS`
- `LANDING_GTFS_STOP_TIMES`
- `LANDING_STREAMING_DEPARTURES`
- `GTFS_LOAD_HISTORY`

### RAW Schema
**Purpose**: Cleaned raw data (from dbt staging models: stg_*)
**Tables**:
- `STG_GTFS_STOPS` (from dbt landing_to_raw)
- `STG_GTFS_ROUTES` (from dbt landing_to_raw)
- `STG_GTFS_TRIPS` (from dbt landing_to_raw)
- `STG_GTFS_STOP_TIMES` (from dbt landing_to_raw)
- `STG_STREAMING_DEPARTURES` (from dbt streaming_to_analytics)

### STAGING Schema
**Purpose**: Staging views/models (dbt staging)
**Tables**: (if any views)

### TRANSFORM Schema
**Purpose**: Intermediate transformations (dbt transform)
**Tables**:
- `ROUTE_DEPARTURES` (from dbt transform)

### ANALYTICS Schema
**Purpose**: Final analytics tables (dbt analytics)
**Tables**:
- `RELIABILITY_METRICS`
- `DEMAND_METRICS`
- `CROWDING_METRICS`
- `REVENUE_METRICS`
- `DECISION_SUPPORT`
- `ROUTE_PERFORMANCE`

### ML Schema
**Purpose**: ML models and forecasts (dbt ml_forecasts)
**Tables**:
- `DEMAND_FORECAST`
- `DELAY_FORECAST`
- `DEMAND_FORECAST_MODEL` (Snowflake ML model)
- `DELAY_FORECAST_MODEL` (Snowflake ML model)

## Files Updated

### Ingestion Scripts
1. `ingestion/fetch_gtfs_incremental.py`
   - All tables now created in `LANDING` schema
   - All queries updated to use `{database}.LANDING.{table}`

2. `ingestion/transit_streaming_producer.py`
   - Streaming data now goes to `LANDING.LANDING_STREAMING_DEPARTURES`

3. `ingestion/kafka_consumer_to_landing.py`
   - Updated to use `LANDING` schema

### dbt Models
1. `dbt/transit_dbt/models/sources.yml`
   - Updated to point to `LANDING` schema for landing tables

2. `dbt/transit_dbt/dbt_project.yml`
   - Added schema configurations:
     - `landing_to_raw` → `RAW` schema
     - `streaming_to_analytics` → `RAW` schema
     - `ml_forecasts` → `ML` schema

### Backend API
1. `api/main.py`
   - All `STG_*` table references → `RAW` schema
   - `LANDING_STREAMING_DEPARTURES` → `LANDING` schema
   - ML tables → `ML` schema
   - Analytics tables → `ANALYTICS` schema

### LLM Chat Handler
1. `api/llm/chat_handler.py`
   - Updated all schema references
   - Improved SQL execution with better error handling
   - Enhanced response generation to provide varied, data-driven responses
   - Fixed issue where same response was returned for all questions

### Airflow DAGs
1. `airflow/dags/ml_forecast_dag.py`
   - **NEW**: Implements actual `CREATE SNOWFLAKE.ML.FORECAST`
   - Creates and trains forecast models for demand and delay
   - Uses `CALL model_name!FORECAST()` to generate predictions
   - Stores results in `ML.DEMAND_FORECAST` and `ML.DELAY_FORECAST` tables

## Snowflake ML FORECAST Implementation

### Demand Forecast Model
- **Model Name**: `{database}.ML.DEMAND_FORECAST_MODEL`
- **Training Data**: Historical departure counts by route and date (last 90 days)
- **Forecast Period**: 7 days ahead
- **Output Table**: `ML.DEMAND_FORECAST`

### Delay Forecast Model
- **Model Name**: `{database}.ML.DELAY_FORECAST_MODEL`
- **Training Data**: Historical delay data from streaming departures (last 90 days)
- **Forecast Period**: 7 days ahead
- **Output Table**: `ML.DELAY_FORECAST`

## Migration Steps

1. **Create Schemas** (if not exists):
   ```sql
   CREATE SCHEMA IF NOT EXISTS LANDING;
   CREATE SCHEMA IF NOT EXISTS RAW;
   CREATE SCHEMA IF NOT EXISTS STAGING;
   CREATE SCHEMA IF NOT EXISTS TRANSFORM;
   CREATE SCHEMA IF NOT EXISTS ANALYTICS;
   CREATE SCHEMA IF NOT EXISTS ML;
   ```

2. **Backup Existing Tables**:
   - Create backup schema
   - Copy existing tables to backup

3. **Move Tables** (if needed):
   - Landing tables: `ANALYTICS.*` → `LANDING.*`
   - Staging tables: `ANALYTICS.STG_*` → `RAW.STG_*`

4. **Run dbt Models**:
   ```bash
   cd dbt/transit_dbt
   dbt run --select landing_to_raw
   dbt run --select streaming_to_analytics
   dbt run --select transform
   dbt run --select analytics
   dbt run --select ml_forecasts
   ```

5. **Run ML Forecast DAG**:
   - Trigger `ml_forecast_dag` in Airflow
   - This will create and train Snowflake ML FORECAST models

## Testing Checklist

- [ ] Verify all schemas exist
- [ ] Verify landing tables are in LANDING schema
- [ ] Verify staging tables are in RAW schema
- [ ] Verify analytics tables are in ANALYTICS schema
- [ ] Verify ML tables are in ML schema
- [ ] Test all API endpoints
- [ ] Test LLM chat handler with various questions
- [ ] Verify ML forecast models are created
- [ ] Verify forecasts are generated and stored

## Notes

- All schema references are now fully qualified: `{database}.{schema}.{table}`
- LLM chat handler now properly executes SQL and returns varied responses based on actual data
- Snowflake ML FORECAST is now properly implemented using `CREATE SNOWFLAKE.ML.FORECAST`
- GTFS data processing: All GTFS files (stops.txt, routes.txt, trips.txt, stop_times.txt) are being processed

