# Schema Mapping Reference

## Proper Schema Structure

### LANDING Schema
- **Purpose**: Raw data from APIs/GTFS (initial ingestion)
- **Tables**:
  - `LANDING_GTFS_STOPS`
  - `LANDING_GTFS_ROUTES`
  - `LANDING_GTFS_TRIPS`
  - `LANDING_GTFS_STOP_TIMES`
  - `LANDING_STREAMING_DEPARTURES`
  - `GTFS_LOAD_HISTORY`

### RAW Schema
- **Purpose**: Cleaned raw data (from dbt staging models: stg_*)
- **Tables**:
  - `STG_GTFS_STOPS` (from dbt landing_to_raw)
  - `STG_GTFS_ROUTES` (from dbt landing_to_raw)
  - `STG_GTFS_TRIPS` (from dbt landing_to_raw)
  - `STG_GTFS_STOP_TIMES` (from dbt landing_to_raw)
  - `STG_STREAMING_DEPARTURES` (from dbt streaming_to_analytics)

### STAGING Schema
- **Purpose**: Staging views/models (dbt staging)
- **Tables**: (if any views)

### TRANSFORM Schema
- **Purpose**: Intermediate transformations (dbt transform)
- **Tables**:
  - `ROUTE_DEPARTURES` (from dbt transform)

### ANALYTICS Schema
- **Purpose**: Final analytics tables (dbt analytics)
- **Tables**:
  - `RELIABILITY_METRICS`
  - `DEMAND_METRICS`
  - `CROWDING_METRICS`
  - `REVENUE_METRICS`
  - `DECISION_SUPPORT`
  - `ROUTE_PERFORMANCE`

### ML Schema
- **Purpose**: ML models and forecasts (dbt ml_forecasts)
- **Tables**:
  - `DEMAND_FORECAST`
  - `DELAY_FORECAST`

## API Endpoint Schema Updates

### Endpoints that query LANDING:
- `/api/admin/status` - Sample data from landing tables

### Endpoints that query RAW:
- `/api/routes` - Uses STG_GTFS_ROUTES, STG_GTFS_STOP_TIMES
- `/api/stops` - Uses STG_GTFS_STOPS, STG_GTFS_STOP_TIMES
- `/api/live-data` - Uses LANDING_STREAMING_DEPARTURES (or STG_STREAMING_DEPARTURES)

### Endpoints that query ANALYTICS:
- `/api/kpis` - Uses RELIABILITY_METRICS, ROUTE_PERFORMANCE
- `/api/analytics/*` - Uses various analytics tables

### Endpoints that query ML:
- `/api/forecasts/demand` - Uses ML.DEMAND_FORECAST
- `/api/forecasts/delay` - Uses ML.DELAY_FORECAST

