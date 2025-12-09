# Transit System - Tables Reference Guide

## Fully Qualified Table Names and Definitions

**Database**: `USER_DB_HORNET`  
**Last Verified**: 2025-12-09

This document provides verified table names with actual data samples from Snowflake.

---

## LANDING Schema
**Purpose**: Raw data ingestion from external sources (GTFS feeds and Transit API)

### `USER_DB_HORNET.LANDING.LANDING_GTFS_STOPS`
- **Definition**: Raw stop data from GTFS feeds (BART, VTA). Contains stop locations, names, and identifiers.
- **Key Columns**: STOP_ID, STOP_NAME, STOP_LAT, STOP_LON, AGENCY, FEED_ID, LOADED_AT
- **Use Case**: Source for stop location mapping and geographic analysis
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.LANDING.LANDING_GTFS_ROUTES`
- **Definition**: Raw route definitions from GTFS feeds. Contains route names, colors, and service types.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, ROUTE_COLOR, AGENCY, FEED_ID, LOADED_AT
- **Use Case**: Route identification and route-level analytics
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.LANDING.LANDING_GTFS_TRIPS`
- **Definition**: Raw trip schedules from GTFS. Links routes to specific service patterns.
- **Key Columns**: TRIP_ID, ROUTE_ID, SERVICE_ID, TRIP_HEADSIGN, AGENCY, FEED_ID, LOADED_AT
- **Use Case**: Trip-level analysis and schedule understanding
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.LANDING.LANDING_GTFS_STOP_TIMES`
- **Definition**: Raw stop time schedules. Contains arrival/departure times for each stop on each trip.
- **Key Columns**: TRIP_ID, STOP_ID, ARRIVAL_TIME, DEPARTURE_TIME, STOP_SEQUENCE, AGENCY, SERVICE_DATE, FEED_ID
- **Use Case**: Schedule analysis, frequency calculations, on-time performance baseline
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.LANDING.LANDING_STREAMING_DEPARTURES`
- **Definition**: Real-time departure data from Transit API. Contains live departure information with delays.
- **Key Columns**: ID, GLOBAL_STOP_ID, STOP_NAME, GLOBAL_ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY, CITY, SCHEDULED_DEPARTURE_TIME, ACTUAL_DEPARTURE_TIME, IS_REAL_TIME, DELAY_SECONDS, CONSUMED_AT
- **Use Case**: Real-time monitoring, delay analysis, on-time performance calculations
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.LANDING.GTFS_LOAD_HISTORY`
- **Definition**: Audit log of GTFS data loads. Tracks when data was ingested.
- **Key Columns**: FEED_ID, AGENCY, LAST_LOAD_DATE, LAST_LOAD_TIMESTAMP, RECORDS_LOADED
- **Use Case**: Data quality monitoring, pipeline health checks
- **Status**: ✅ Verified with data

---

## ANALYTICS_RAW Schema
**Purpose**: Cleaned and standardized raw data (staging layer from dbt)

### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_STOPS`
- **Definition**: Cleaned stop data with standardized column names and data types.
- **Key Columns**: STOP_ID, STOP_NAME, STOP_LAT, STOP_LON, AGENCY, LOADED_AT
- **Use Case**: Primary source for stop-related queries and joins
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_ROUTES`
- **Definition**: Cleaned route data with standardized formats.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, ROUTE_COLOR, AGENCY, LOADED_AT
- **Use Case**: Route identification and route-level metrics
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_TRIPS`
- **Definition**: Cleaned trip data with standardized formats.
- **Key Columns**: TRIP_ID, ROUTE_ID, SERVICE_ID, TRIP_HEADSIGN, AGENCY, LOADED_AT
- **Use Case**: Trip-level joins and analysis
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.ANALYTICS_RAW.STG_GTFS_STOP_TIMES`
- **Definition**: Cleaned stop time data with standardized time formats.
- **Key Columns**: TRIP_ID, STOP_ID, ARRIVAL_TIME, DEPARTURE_TIME, STOP_SEQUENCE, AGENCY, SERVICE_DATE, LOADED_AT
- **Use Case**: Schedule analysis, frequency calculations, hourly demand patterns
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.ANALYTICS_RAW.STG_STREAMING_DEPARTURES`
- **Definition**: Cleaned streaming departure data with standardized formats.
- **Key Columns**: ID, TIMESTAMP, STOP_ID, STOP_NAME, ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY, SCHEDULED_DEPARTURE_TIME, ACTUAL_DEPARTURE_TIME, DELAY_SECONDS, IS_REAL_TIME, LOAD_TIMESTAMP
- **Use Case**: Real-time analytics, delay tracking, on-time performance
- **Status**: ⚠️ Table exists but currently empty (will be populated by streaming pipeline)

---

## ANALYTICS_TRANSFORM Schema
**Purpose**: Business logic transformations and enriched data

### `USER_DB_HORNET.ANALYTICS_TRANSFORM.ROUTE_DEPARTURES`
- **Definition**: Enriched departure data combining GTFS schedules with route and stop information.
- **Key Columns**: TRIP_ID, STOP_ID, ROUTE_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, STOP_NAME, DEPARTURE_TIME, AGENCY, SERVICE_DATE
- **Use Case**: Route performance analysis, stop utilization, departure frequency
- **Status**: ✅ Verified with data

---

## ANALYTICS_ANALYTICS Schema
**Purpose**: Final analytics tables for dashboards and reporting

### `USER_DB_HORNET.ANALYTICS_ANALYTICS.RELIABILITY_METRICS`
- **Definition**: Calculated reliability metrics per route and stop. Includes on-time performance, average delays, and reliability scores.
- **Key Columns**: ID, ROUTE_GLOBAL_ID, ROUTE_SHORT_NAME, DEPARTURE_DATE, DEPARTURE_HOUR, TOTAL_DEPARTURES, ON_TIME_DEPARTURES, EARLY_DEPARTURES, LATE_DEPARTURES, VERY_LATE_DEPARTURES, ON_TIME_PCT, AVG_DELAY_SECONDS, MEDIAN_DELAY_SECONDS, RELIABILITY_SCORE, AGENCY, LAST_UPDATE
- **Use Case**: Dashboard KPIs, route health monitoring, service quality metrics
- **Status**: ⚠️ Table exists but currently empty (will be populated by analytics pipeline)

### `USER_DB_HORNET.ANALYTICS_ANALYTICS.DEMAND_METRICS`
- **Definition**: Demand analysis metrics showing departure frequency, passenger estimates, and peak hours.
- **Key Columns**: ID, STOP_GLOBAL_ID, STOP_NAME, STOP_LAT, STOP_LON, LOCATION_TYPE, PARENT_STATION_NAME, ROUTE_GLOBAL_ID, ROUTE_SHORT_NAME, TIME_PERIOD, DEPARTURE_COUNT, PASSENGER_COUNT, DEMAND_SCORE, AGENCY, UPDATED_AT
- **Use Case**: Capacity planning, peak hour analysis, route optimization
- **Status**: ⚠️ Table exists but currently empty (will be populated by analytics pipeline)

### `USER_DB_HORNET.ANALYTICS_ANALYTICS.CROWDING_METRICS`
- **Definition**: Estimated crowding levels based on departure frequency and historical patterns.
- **Key Columns**: ID, ROUTE_GLOBAL_ID, ROUTE_SHORT_NAME, DEPARTURE_DATE, DEPARTURE_HOUR, TOTAL_DEPARTURES, REALTIME_DEPARTURES, AVG_OCCUPANCY_RATIO, CROWDING_LEVEL, AGENCY, UPDATED_AT
- **Use Case**: Capacity management, passenger experience optimization
- **Status**: ⚠️ Table exists but currently empty (will be populated by analytics pipeline)

### `USER_DB_HORNET.ANALYTICS_ANALYTICS.REVENUE_METRICS`
- **Definition**: Estimated revenue calculations based on departures and average fares.
- **Key Columns**: ID, ROUTE_GLOBAL_ID, ROUTE_SHORT_NAME, DEPARTURE_DATE, DEPARTURE_COUNT, ESTIMATED_RIDERSHIP, AVG_FARE, ESTIMATED_REVENUE, ESTIMATED_DAILY_REVENUE, ESTIMATED_MONTHLY_REVENUE, AGENCY, UPDATED_AT
- **Use Case**: Financial analysis, route profitability assessment
- **Status**: ⚠️ Table exists but currently empty (will be populated by analytics pipeline)

### `USER_DB_HORNET.ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE`
- **Definition**: Comprehensive route performance metrics combining reliability, demand, and utilization.
- **Key Columns**: ROUTE_ID, AGENCY, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, TOTAL_TRIPS, TOTAL_STOPS, TOTAL_DEPARTURES, STREAMING_DEPARTURES, AVG_DELAY_SECONDS, ON_TIME_PERFORMANCE, UPDATED_AT
- **Use Case**: Route comparison, performance ranking, decision support
- **Status**: ✅ Verified with data

### `USER_DB_HORNET.ANALYTICS_ANALYTICS.DECISION_SUPPORT`
- **Definition**: AI-ready recommendations and insights for operations teams.
- **Key Columns**: ID, ROUTE_GLOBAL_ID, ROUTE_SHORT_NAME, ON_TIME_PCT, AVG_DELAY_MINUTES, RELIABILITY_SCORE, AVG_HEADWAY_MINUTES, AVG_DAILY_DEPARTURES, RECOMMENDATION_TYPE, SEVERITY, IMPACT, ESTIMATED_SAVINGS, AGENCY, UPDATED_AT
- **Use Case**: Operational decision making, resource allocation, optimization suggestions
- **Status**: ⚠️ Table exists but currently empty (will be populated by analytics pipeline)

---

## ANALYTICS_ML Schema
**Purpose**: Machine learning predictions and forecasts

### `USER_DB_HORNET.ANALYTICS_ML.DEMAND_FORECAST`
- **Definition**: ML-generated demand forecasts for future departures using Snowflake ML FORECAST.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, AGENCY, FORECAST_DATE, PREDICTED_DEPARTURES, FORECAST_GENERATED_AT
- **Use Case**: Capacity planning, resource allocation, demand prediction
- **Status**: ✅ Verified (may be empty if ML pipeline hasn't run)

### `USER_DB_HORNET.ANALYTICS_ML.DELAY_FORECAST`
- **Definition**: ML-generated delay predictions for routes using historical delay patterns.
- **Key Columns**: ROUTE_ID, ROUTE_SHORT_NAME, AGENCY, FORECAST_DATE, PREDICTED_AVG_DELAY, PREDICTED_MEDIAN_DELAY, FORECAST_GENERATED_AT
- **Use Case**: Proactive delay management, schedule adjustments, passenger communication
- **Status**: ⚠️ Table exists but currently empty (will be populated when ML pipeline runs with sufficient delay data)

---

## Table Relationships

### Data Flow:
1. **LANDING** → Raw ingestion from external sources
2. **ANALYTICS_RAW** → Cleaned and standardized (dbt staging)
3. **ANALYTICS_TRANSFORM** → Business logic applied (dbt transform)
4. **ANALYTICS_ANALYTICS** → Final metrics and KPIs (dbt analytics)
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
- Use: `ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE` - Comprehensive route metrics
- Use: `ANALYTICS_ANALYTICS.RELIABILITY_METRICS` - On-time performance details
- Use: `ANALYTICS_ML.DEMAND_FORECAST` - Future demand predictions

### For Stop Analytics:
- Use: `ANALYTICS_RAW.STG_GTFS_STOPS` - Stop locations and names
- Use: `ANALYTICS_ANALYTICS.RELIABILITY_METRICS` - Stop-level performance
- Use: `ANALYTICS_ANALYTICS.DEMAND_METRICS` - Stop-level demand patterns

### For Real-Time Monitoring:
- Use: `LANDING.LANDING_STREAMING_DEPARTURES` - Live departure data
- Use: `ANALYTICS_ANALYTICS.RELIABILITY_METRICS` - Current performance metrics

### For Forecasting:
- Use: `ANALYTICS_ML.DEMAND_FORECAST` - Departure demand predictions
- Use: `ANALYTICS_ML.DELAY_FORECAST` - Delay predictions

---

## Notes for Dashboard Creation:
1. Always filter by `AGENCY` (BART or VTA) when needed
2. Use `UPDATED_AT`, `LAST_UPDATE`, or `CONSUMED_AT` for time-based filtering
3. Join on `ROUTE_ID` and `STOP_ID` for detailed analysis
4. `ANALYTICS_ANALYTICS` schema tables are optimized for dashboard queries
5. ML tables update daily via Airflow DAGs
6. All table names are verified and exist in Snowflake (as of 2025-12-09)
7. **Status Legend**:
   - ✅ = Table exists with data
   - ⚠️ = Table exists but currently empty (will be populated by pipelines)
8. **Current Data Status**:
   - **LANDING**: 6 tables with data (3,617 stops, 87 routes, 12,356 trips, 419,686 stop times, 100 streaming departures)
   - **ANALYTICS_RAW**: 4 tables with data, 1 empty (STG_STREAMING_DEPARTURES)
   - **ANALYTICS_TRANSFORM**: 1 table with 29M+ records (ROUTE_DEPARTURES)
   - **ANALYTICS_ANALYTICS**: 1 table with data (ROUTE_PERFORMANCE), 5 empty (will populate via dbt)
   - **ANALYTICS_ML**: 1 table with data (DEMAND_FORECAST), 1 empty (DELAY_FORECAST)

---

## Sample Queries

### Get Route Performance:
```sql
SELECT 
    ROUTE_SHORT_NAME,
    ROUTE_LONG_NAME,
    AGENCY,
    TOTAL_DEPARTURES,
    ON_TIME_PERFORMANCE,
    AVG_DELAY_SECONDS
FROM USER_DB_HORNET.ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE
WHERE AGENCY = 'BART'  -- or 'VTA'
ORDER BY ON_TIME_PERFORMANCE DESC
```

### Get Reliability Metrics by Hour:
```sql
SELECT 
    ROUTE_SHORT_NAME,
    DEPARTURE_HOUR,
    ON_TIME_PCT,
    RELIABILITY_SCORE,
    TOTAL_DEPARTURES
FROM USER_DB_HORNET.ANALYTICS_ANALYTICS.RELIABILITY_METRICS
WHERE DEPARTURE_DATE >= CURRENT_DATE() - 7
ORDER BY DEPARTURE_HOUR, ROUTE_SHORT_NAME
```

### Get Forecasts:
```sql
SELECT 
    ROUTE_SHORT_NAME,
    AGENCY,
    FORECAST_DATE,
    PREDICTED_DEPARTURES
FROM USER_DB_HORNET.ANALYTICS_ML.DEMAND_FORECAST
WHERE FORECAST_DATE >= CURRENT_DATE()
ORDER BY FORECAST_DATE, ROUTE_SHORT_NAME
```

---

**Last Updated**: 2025-12-09  
**All tables verified with actual data samples from Snowflake**
