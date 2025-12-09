# Transit System - Tables Reference Guide

## Fully Qualified Table Names and Definitions

### LANDING Schema
**Purpose**: Raw data ingestion from external sources (GTFS feeds and Transit API)

#### `USER_DB_HORNET.LANDING.LANDING_GTFS_STOPS`
- **Definition**: Raw stop data from GTFS feeds (BART, VTA). Contains stop locations, names, and identifiers.
- **Key Columns**: STOP_ID, STOP_NAME, STOP_LAT, STOP_LON, AGENCY
- **Use Case**: Source for stop location mapping and geographic analysis

#### `USER_DB_HORNET.LANDING.LANDING_GTFS_ROUTES`
- **Definition**: Raw route definitions from GTFS feeds. Contains route names, colors, and service types.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, ROUTE_COLOR, AGENCY
- **Use Case**: Route identification and route-level analytics

#### `USER_DB_HORNET.LANDING.LANDING_GTFS_TRIPS`
- **Definition**: Raw trip schedules from GTFS. Links routes to specific service patterns.
- **Key Columns**: TRIP_ID, ROUTE_ID, SERVICE_ID, TRIP_HEADSIGN, AGENCY
- **Use Case**: Trip-level analysis and schedule understanding

#### `USER_DB_HORNET.LANDING.LANDING_GTFS_STOP_TIMES`
- **Definition**: Raw stop time schedules. Contains arrival/departure times for each stop on each trip.
- **Key Columns**: TRIP_ID, STOP_ID, ARRIVAL_TIME, DEPARTURE_TIME, STOP_SEQUENCE, AGENCY
- **Use Case**: Schedule analysis, frequency calculations, on-time performance baseline

#### `USER_DB_HORNET.LANDING.LANDING_STREAMING_DEPARTURES`
- **Definition**: Real-time departure data from Transit API. Contains live departure information with delays.
- **Key Columns**: STOP_ID, ROUTE_ID, SCHEDULED_DEPARTURE_TIME, ACTUAL_DEPARTURE_TIME, DELAY_SECONDS, IS_REAL_TIME, AGENCY, CONSUMED_AT
- **Use Case**: Real-time monitoring, delay analysis, on-time performance calculations

#### `USER_DB_HORNET.LANDING.GTFS_LOAD_HISTORY`
- **Definition**: Audit log of GTFS data loads. Tracks when data was ingested.
- **Key Columns**: LOAD_DATE, AGENCY, RECORD_COUNT, STATUS
- **Use Case**: Data quality monitoring, pipeline health checks

---

### ANALYTICS_RAW Schema
**Purpose**: Cleaned and standardized raw data (staging layer from dbt)

#### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_STOPS`
- **Definition**: Cleaned stop data with standardized column names and data types.
- **Key Columns**: STOP_ID, STOP_NAME, STOP_LAT, STOP_LON, AGENCY, LOADED_AT
- **Use Case**: Primary source for stop-related queries and joins

#### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_ROUTES`
- **Definition**: Cleaned route data with standardized formats.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, ROUTE_COLOR, AGENCY, LOADED_AT
- **Use Case**: Route identification and route-level metrics

#### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_TRIPS`
- **Definition**: Cleaned trip data with standardized formats.
- **Key Columns**: TRIP_ID, ROUTE_ID, SERVICE_ID, TRIP_HEADSIGN, AGENCY, LOADED_AT
- **Use Case**: Trip-level joins and analysis

#### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_STOP_TIMES`
- **Definition**: Cleaned stop time data with standardized time formats.
- **Key Columns**: TRIP_ID, STOP_ID, ARRIVAL_TIME, DEPARTURE_TIME, STOP_SEQUENCE, AGENCY, LOADED_AT
- **Use Case**: Schedule analysis, frequency calculations, hourly demand patterns

#### `USER_DB_HORNET.ANALYTICS_RAW.STG_STREAMING_DEPARTURES`
- **Definition**: Cleaned streaming departure data with standardized formats.
- **Key Columns**: STOP_ID, ROUTE_ID, SCHEDULED_DEPARTURE_TIME, ACTUAL_DEPARTURE_TIME, DELAY_SECONDS, IS_REAL_TIME, AGENCY, LOAD_TIMESTAMP
- **Use Case**: Real-time analytics, delay tracking, on-time performance

---

### TRANSFORM Schema
**Purpose**: Business logic transformations and enriched data

#### `USER_DB_HORNET.ANALYTICS_TRANSFORM.ROUTE_DEPARTURES`
- **Definition**: Enriched departure data combining GTFS schedules with route and stop information.
- **Key Columns**: TRIP_ID, STOP_ID, ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, STOP_NAME, DEPARTURE_TIME, AGENCY
- **Use Case**: Route performance analysis, stop utilization, departure frequency

---

### ANALYTICS Schema
**Purpose**: Final analytics tables for dashboards and reporting

#### `USER_DB_HORNET.ANALYTICS.RELIABILITY_METRICS`
- **Definition**: Calculated reliability metrics per route and stop. Includes on-time performance, average delays, and reliability scores.
- **Key Columns**: ROUTE_ID, STOP_ID, ON_TIME_PCT, AVG_DELAY_SECONDS, RELIABILITY_SCORE, AGENCY, UPDATED_AT
- **Use Case**: Dashboard KPIs, route health monitoring, service quality metrics

#### `USER_DB_HORNET.ANALYTICS.DEMAND_METRICS`
- **Definition**: Demand analysis metrics showing departure frequency, passenger estimates, and peak hours.
- **Key Columns**: ROUTE_ID, STOP_ID, HOURLY_DEPARTURES, PEAK_HOUR, DEMAND_SCORE, AGENCY, UPDATED_AT
- **Use Case**: Capacity planning, peak hour analysis, route optimization

#### `USER_DB_HORNET.ANALYTICS.CROWDING_METRICS`
- **Definition**: Estimated crowding levels based on departure frequency and historical patterns.
- **Key Columns**: ROUTE_ID, STOP_ID, OCCUPANCY_RATIO, CROWDING_LEVEL, AGENCY, UPDATED_AT
- **Use Case**: Capacity management, passenger experience optimization

#### `USER_DB_HORNET.ANALYTICS.REVENUE_METRICS`
- **Definition**: Estimated revenue calculations based on departures and average fares.
- **Key Columns**: ROUTE_ID, ESTIMATED_DAILY_REVENUE, ESTIMATED_MONTHLY_REVENUE, AGENCY, UPDATED_AT
- **Use Case**: Financial analysis, route profitability assessment

#### `USER_DB_HORNET.ANALYTICS.ROUTE_PERFORMANCE`
- **Definition**: Comprehensive route performance metrics combining reliability, demand, and utilization.
- **Key Columns**: ROUTE_ID, ROUTE_NAME, TOTAL_TRIPS, TOTAL_STOPS, TOTAL_DEPARTURES, STREAMING_DEPARTURES, AVG_DELAY_SECONDS, ON_TIME_PERFORMANCE, AGENCY, UPDATED_AT
- **Use Case**: Route comparison, performance ranking, decision support

#### `USER_DB_HORNET.ANALYTICS.DECISION_SUPPORT`
- **Definition**: AI-ready recommendations and insights for operations teams.
- **Key Columns**: ROUTE_ID, RECOMMENDATION_TYPE, SEVERITY, IMPACT, ESTIMATED_SAVINGS, AGENCY, UPDATED_AT
- **Use Case**: Operational decision making, resource allocation, optimization suggestions

---

### ANALYTICS_ML Schema
**Purpose**: Machine learning predictions and forecasts

#### `USER_DB_HORNET.ANALYTICS_ML.DEMAND_FORECAST`
- **Definition**: ML-generated demand forecasts for future departures using Snowflake ML FORECAST.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, AGENCY, FORECAST_DATE, PREDICTED_DEPARTURES, FORECAST_GENERATED_AT
- **Use Case**: Capacity planning, resource allocation, demand prediction

#### `USER_DB_HORNET.ANALYTICS_ML.DELAY_FORECAST`
- **Definition**: ML-generated delay predictions for routes using historical delay patterns.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, AGENCY, FORECAST_DATE, PREDICTED_AVG_DELAY, PREDICTED_MEDIAN_DELAY, FORECAST_GENERATED_AT
- **Use Case**: Proactive delay management, schedule adjustments, passenger communication

---

## Table Relationships

### Data Flow:
1. **LANDING** → Raw ingestion from external sources
2. **ANALYTICS_RAW** → Cleaned and standardized (dbt staging)
3. **TRANSFORM** → Business logic applied (dbt transform)
4. **ANALYTICS** → Final metrics and KPIs (dbt analytics)
5. **ANALYTICS_ML** → ML predictions (Snowflake ML)

### Key Relationships:
- `STG_GTFS_STOPS` ↔ `STG_GTFS_STOP_TIMES` (via STOP_ID)
- `STG_GTFS_ROUTES` ↔ `STG_GTFS_TRIPS` (via ROUTE_ID)
- `STG_GTFS_TRIPS` ↔ `STG_GTFS_STOP_TIMES` (via TRIP_ID)
- `STG_STREAMING_DEPARTURES` → `RELIABILITY_METRICS` (delay calculations)
- `ROUTE_DEPARTURES` → `ROUTE_PERFORMANCE` (aggregations)
- All analytics tables include `AGENCY` for filtering (BART, VTA)

---

## Dashboard Usage Guidelines

### For Route Analytics:
- Use: `ANALYTICS.ROUTE_PERFORMANCE` - Comprehensive route metrics
- Use: `ANALYTICS.RELIABILITY_METRICS` - On-time performance details
- Use: `ANALYTICS_ML.DEMAND_FORECAST` - Future demand predictions

### For Stop Analytics:
- Use: `ANALYTICS_RAW.STG_GTFS_STOPS` - Stop locations and names
- Use: `ANALYTICS.RELIABILITY_METRICS` - Stop-level performance
- Use: `ANALYTICS.DEMAND_METRICS` - Stop-level demand patterns

### For Real-Time Monitoring:
- Use: `LANDING.LANDING_STREAMING_DEPARTURES` - Live departure data
- Use: `ANALYTICS.RELIABILITY_METRICS` - Current performance metrics

### For Forecasting:
- Use: `ANALYTICS_ML.DEMAND_FORECAST` - Departure demand predictions
- Use: `ANALYTICS_ML.DELAY_FORECAST` - Delay predictions

---

## Notes for Dashboard Creation:
1. Always filter by `AGENCY` (BART or VTA) when needed
2. Use `UPDATED_AT` or `CONSUMED_AT` for time-based filtering
3. Join on `ROUTE_ID` and `STOP_ID` for detailed analysis
4. `ANALYTICS` schema tables are optimized for dashboard queries
5. ML tables update daily via Airflow DAGs

