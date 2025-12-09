# Tableau Dashboard - Data Tables Reference

**For**: Tableau Dashboard Developer  
**Database**: `USER_DB_HORNET`  
**Last Updated**: 2025-01-08

This document provides a comprehensive list of all tables available for Tableau dashboard development, organized by schema and purpose.

---

## Quick Reference: All Tables

### Total: **20 tables** across **5 schemas**

| Schema | Table Count | Purpose |
|--------|-------------|---------|
| LANDING | 6 | Raw data from APIs/GTFS |
| RAW | 5 | Cleaned raw data |
| TRANSFORM | 1 | Intermediate transformations |
| ANALYTICS | 6 | Final analytics tables |
| ML | 2 | ML forecasts |

---

## Database: `USER_DB_HORNET`

---

## LANDING Schema
**Purpose**: Raw data from APIs/GTFS (initial ingestion layer)

### Tables:

#### `LANDING_GTFS_STOPS`
**Description**: GTFS stops data from transit agencies (BART, VTA)
**Key Columns**:
- `STOP_ID` (VARCHAR): Unique stop identifier
- `STOP_NAME` (VARCHAR): Stop name
- `STOP_LAT` (FLOAT): Latitude
- `STOP_LON` (FLOAT): Longitude
- `AGENCY` (VARCHAR): Transit agency (BART, VTA)
- `FEED_ID` (VARCHAR): Feed identifier
- `LOADED_AT` (TIMESTAMP): When data was loaded

**Use Case**: Map visualization, stop locations, geographic analysis

---

#### `LANDING_GTFS_ROUTES`
**Description**: GTFS routes data
**Key Columns**:
- `ROUTE_ID` (VARCHAR): Unique route identifier
- `ROUTE_SHORT_NAME` (VARCHAR): Short route name (e.g., "22", "Yellow-S")
- `ROUTE_LONG_NAME` (VARCHAR): Full route name (e.g., "Antioch to SF Int'l Airport SFO")
- `ROUTE_COLOR` (VARCHAR): Hex color code
- `AGENCY` (VARCHAR): Transit agency (BART, VTA)
- `FEED_ID` (VARCHAR): Feed identifier
- `LOADED_AT` (TIMESTAMP): When data was loaded

**Use Case**: Route listings, route performance analysis

---

#### `LANDING_GTFS_TRIPS`
**Description**: GTFS trips data
**Key Columns**:
- `TRIP_ID` (VARCHAR): Unique trip identifier
- `ROUTE_ID` (VARCHAR): Route identifier
- `SERVICE_ID` (VARCHAR): Service pattern identifier
- `AGENCY` (VARCHAR): Transit agency
- `FEED_ID` (VARCHAR): Feed identifier
- `LOADED_AT` (TIMESTAMP): When data was loaded

**Use Case**: Trip analysis, service patterns

---

#### `LANDING_GTFS_STOP_TIMES`
**Description**: GTFS stop times (scheduled departures)
**Key Columns**:
- `TRIP_ID` (VARCHAR): Trip identifier
- `STOP_ID` (VARCHAR): Stop identifier
- `ARRIVAL_TIME` (TIME): Scheduled arrival time
- `DEPARTURE_TIME` (TIME): Scheduled departure time
- `STOP_SEQUENCE` (INTEGER): Stop sequence in trip
- `AGENCY` (VARCHAR): Transit agency
- `SERVICE_DATE` (DATE): Service date
- `FEED_ID` (VARCHAR): Feed identifier

**Use Case**: Schedule analysis, departure frequency, service planning

---

#### `LANDING_STREAMING_DEPARTURES`
**Description**: Real-time departure data from Transit API
**Key Columns**:
- `ID` (VARCHAR): Unique record identifier
- `GLOBAL_STOP_ID` (VARCHAR): Stop identifier
- `STOP_NAME` (VARCHAR): Stop name
- `GLOBAL_ROUTE_ID` (VARCHAR): Route identifier
- `ROUTE_SHORT_NAME` (VARCHAR): Route short name
- `ROUTE_LONG_NAME` (VARCHAR): Route long name
- `AGENCY` (VARCHAR): Transit agency (BART, VTA)
- `CITY` (VARCHAR): City name
- `SCHEDULED_DEPARTURE_TIME` (BIGINT): Epoch timestamp
- `DEPARTURE_TIME` (BIGINT): Actual/predicted epoch timestamp
- `DELAY_SECONDS` (INTEGER): Delay in seconds (negative = early)
- `IS_REAL_TIME` (BOOLEAN): Whether data is real-time
- `CONSUMED_AT` (TIMESTAMP): When data was loaded

**Use Case**: Real-time dashboards, delay analysis, on-time performance

---

#### `GTFS_LOAD_HISTORY`
**Description**: History of GTFS data loads
**Key Columns**:
- `FEED_ID` (VARCHAR): Feed identifier
- `AGENCY` (VARCHAR): Transit agency
- `LAST_LOAD_DATE` (DATE): Last load date
- `LAST_LOAD_TIMESTAMP` (TIMESTAMP): Last load timestamp
- `RECORDS_LOADED` (INTEGER): Number of records loaded

**Use Case**: Data freshness tracking, ETL monitoring

---

## RAW Schema
**Purpose**: Cleaned raw data (from dbt staging models)

### Tables:

#### `STG_GTFS_STOPS`
**Description**: Cleaned GTFS stops (from `landing_to_raw` dbt model)
**Key Columns**: Same as `LANDING_GTFS_STOPS` but cleaned and validated
**Use Case**: Primary source for stop data in dashboards

---

#### `STG_GTFS_ROUTES`
**Description**: Cleaned GTFS routes (from `landing_to_raw` dbt model)
**Key Columns**: Same as `LANDING_GTFS_ROUTES` but cleaned and validated
**Use Case**: Primary source for route data in dashboards

---

#### `STG_GTFS_TRIPS`
**Description**: Cleaned GTFS trips (from `landing_to_raw` dbt model)
**Key Columns**: Same as `LANDING_GTFS_TRIPS` but cleaned and validated
**Use Case**: Trip analysis

---

#### `STG_GTFS_STOP_TIMES`
**Description**: Cleaned GTFS stop times (from `landing_to_raw` dbt model)
**Key Columns**: Same as `LANDING_GTFS_STOP_TIMES` but cleaned and validated
**Use Case**: Schedule analysis, departure frequency

---

#### `STG_STREAMING_DEPARTURES`
**Description**: Cleaned streaming departures (from `streaming_to_analytics` dbt model)
**Key Columns**: 
- `ID` (VARCHAR): Unique identifier
- `STOP_ID` (VARCHAR): Stop identifier
- `STOP_NAME` (VARCHAR): Stop name
- `ROUTE_ID` (VARCHAR): Route identifier
- `ROUTE_SHORT_NAME` (VARCHAR): Route short name
- `ROUTE_LONG_NAME` (VARCHAR): Route long name
- `AGENCY` (VARCHAR): Transit agency
- `SCHEDULED_DEPARTURE_TIME` (BIGINT): Scheduled time (epoch)
- `ACTUAL_DEPARTURE_TIME` (BIGINT): Actual time (epoch)
- `DELAY_SECONDS` (INTEGER): Delay in seconds
- `LOAD_TIMESTAMP` (TIMESTAMP): When data was loaded

**Use Case**: Real-time performance metrics, delay analysis

---

## TRANSFORM Schema
**Purpose**: Intermediate transformations

### Tables:

#### `ROUTE_DEPARTURES`
**Description**: Aggregated route departure data (from `transform` dbt model)
**Key Columns**:
- `ROUTE_ID` (VARCHAR): Route identifier
- `AGENCY` (VARCHAR): Transit agency
- `TRIP_ID` (VARCHAR): Trip identifier
- `STOP_ID` (VARCHAR): Stop identifier
- Additional aggregated metrics

**Use Case**: Route-level aggregations, intermediate calculations

---

## ANALYTICS Schema
**Purpose**: Final analytics tables (ready for dashboards)

### Tables:

#### `RELIABILITY_METRICS`
**Description**: Service reliability metrics by route and hour
**Key Columns**:
- `ID` (VARCHAR): Unique identifier
- `ROUTE_GLOBAL_ID` (VARCHAR): Route identifier
- `ROUTE_SHORT_NAME` (VARCHAR): Route short name
- `DEPARTURE_DATE` (DATE): Date
- `DEPARTURE_HOUR` (INTEGER): Hour (0-23)
- `TOTAL_DEPARTURES` (INTEGER): Total departures
- `ON_TIME_DEPARTURES` (INTEGER): On-time departures
- `EARLY_DEPARTURES` (INTEGER): Early departures
- `LATE_DEPARTURES` (INTEGER): Late departures
- `VERY_LATE_DEPARTURES` (INTEGER): Very late departures
- `ON_TIME_PCT` (FLOAT): On-time percentage (0-100)
- `AVG_DELAY_SECONDS` (FLOAT): Average delay in seconds
- `MEDIAN_DELAY_SECONDS` (FLOAT): Median delay in seconds
- `AVG_HEADWAY_MINUTES` (FLOAT): Average headway in minutes
- `RELIABILITY_SCORE` (FLOAT): Overall reliability score (0-100)
- `LAST_UPDATE` (TIMESTAMP): Last update timestamp

**Use Case**: **PRIMARY TABLE FOR RELIABILITY DASHBOARDS**
- On-time performance trends
- Hourly reliability patterns
- Route comparison
- Service quality metrics

---

#### `DEMAND_METRICS`
**Description**: Demand metrics by route and time period
**Key Columns**:
- `ID` (VARCHAR): Unique identifier
- `ROUTE_ID` (VARCHAR): Route identifier
- `AGENCY` (VARCHAR): Transit agency
- `TIME_PERIOD` (VARCHAR): Time period
- `DEPARTURE_COUNT` (INTEGER): Number of departures
- `PASSENGER_COUNT` (INTEGER): Estimated passenger count
- `UTILIZATION_PCT` (FLOAT): Utilization percentage
- Additional demand metrics

**Use Case**: Demand analysis, capacity planning, peak hour identification

---

#### `CROWDING_METRICS`
**Description**: Crowding metrics by route and stop
**Key Columns**:
- `ID` (VARCHAR): Unique identifier
- `ROUTE_ID` (VARCHAR): Route identifier
- `STOP_ID` (VARCHAR): Stop identifier
- `CROWDING_LEVEL` (VARCHAR): Crowding level (Low, Medium, High)
- `PASSENGER_COUNT` (INTEGER): Passenger count
- Additional crowding metrics

**Use Case**: Capacity analysis, crowding hotspots

---

#### `REVENUE_METRICS`
**Description**: Revenue metrics by route
**Key Columns**:
- `ID` (VARCHAR): Unique identifier
- `ROUTE_ID` (VARCHAR): Route identifier
- `AGENCY` (VARCHAR): Transit agency
- `ESTIMATED_DAILY_REVENUE` (FLOAT): Estimated daily revenue
- `ESTIMATED_MONTHLY_REVENUE` (FLOAT): Estimated monthly revenue
- `FARE_COLLECTED` (FLOAT): Fare collected
- Additional revenue metrics

**Use Case**: Revenue analysis, financial dashboards

---

#### `DECISION_SUPPORT`
**Description**: Decision support metrics and recommendations
**Key Columns**:
- `ID` (VARCHAR): Unique identifier
- `ROUTE_ID` (VARCHAR): Route identifier
- `AGENCY` (VARCHAR): Transit agency
- `METRIC_TYPE` (VARCHAR): Metric type
- `METRIC_VALUE` (FLOAT): Metric value
- `RECOMMENDATION` (VARCHAR): AI recommendation
- `SEVERITY` (VARCHAR): Severity level (🟢🟡🔴)
- Additional decision support fields

**Use Case**: Executive dashboards, decision support, recommendations

---

#### `ROUTE_PERFORMANCE`
**Description**: Comprehensive route performance metrics
**Key Columns**:
- `ROUTE_ID` (VARCHAR): Route identifier
- `AGENCY` (VARCHAR): Transit agency
- `ROUTE_SHORT_NAME` (VARCHAR): Route short name
- `ROUTE_LONG_NAME` (VARCHAR): Route long name
- `TOTAL_TRIPS` (INTEGER): Total trips
- `TOTAL_STOPS` (INTEGER): Total stops served
- `TOTAL_DEPARTURES` (INTEGER): Total departures
- `STREAMING_DEPARTURES` (INTEGER): Streaming departures count
- `AVG_DELAY_SECONDS` (FLOAT): Average delay in seconds
- `ON_TIME_PERFORMANCE` (FLOAT): On-time performance percentage
- `UPDATED_AT` (TIMESTAMP): Last update timestamp

**Use Case**: **PRIMARY TABLE FOR ROUTE PERFORMANCE DASHBOARDS**
- Route comparison
- Performance rankings
- Agency-level metrics

---

## ML Schema
**Purpose**: ML models and forecasts

### Tables:

#### `DEMAND_FORECAST`
**Description**: Demand forecasts using Snowflake ML FORECAST
**Key Columns**:
- `ROUTE_ID` (VARCHAR): Route identifier
- `ROUTE_SHORT_NAME` (VARCHAR): Route short name
- `AGENCY` (VARCHAR): Transit agency
- `FORECAST_DATE` (DATE): Forecast date
- `PREDICTED_DEPARTURES` (INTEGER): Predicted number of departures
- `FORECAST_GENERATED_AT` (TIMESTAMP): When forecast was generated

**Use Case**: **PRIMARY TABLE FOR FORECASTING DASHBOARDS**
- Future demand predictions
- Capacity planning
- Resource allocation

---

#### `DELAY_FORECAST`
**Description**: Delay forecasts using Snowflake ML FORECAST
**Key Columns**:
- `ROUTE_ID` (VARCHAR): Route identifier
- `ROUTE_SHORT_NAME` (VARCHAR): Route short name
- `AGENCY` (VARCHAR): Transit agency
- `FORECAST_DATE` (DATE): Forecast date
- `PREDICTED_AVG_DELAY` (FLOAT): Predicted average delay in seconds
- `PREDICTED_MEDIAN_DELAY` (FLOAT): Predicted median delay in seconds
- `FORECAST_GENERATED_AT` (TIMESTAMP): When forecast was generated

**Use Case**: **PRIMARY TABLE FOR DELAY PREDICTION DASHBOARDS**
- Future delay predictions
- Proactive service management
- Performance planning

---

## Recommended Tableau Data Sources

### For Main Dashboard:
1. **`ANALYTICS.RELIABILITY_METRICS`** - Primary reliability metrics
2. **`ANALYTICS.ROUTE_PERFORMANCE`** - Route-level performance
3. **`RAW.STG_STREAMING_DEPARTURES`** - Real-time data

### For Forecasting Dashboard:
1. **`ML.DEMAND_FORECAST`** - Demand predictions
2. **`ML.DELAY_FORECAST`** - Delay predictions

### For Map Visualization:
1. **`RAW.STG_GTFS_STOPS`** - Stop locations
2. **`RAW.STG_GTFS_ROUTES`** - Route information
3. **`RAW.STG_STREAMING_DEPARTURES`** - Real-time departures

### For Revenue Dashboard:
1. **`ANALYTICS.REVENUE_METRICS`** - Revenue data
2. **`ANALYTICS.ROUTE_PERFORMANCE`** - Route metrics

---

## Connection String Template

```
Server: <your-snowflake-account>.snowflakecomputing.com
Database: USER_DB_HORNET
Schema: <schema_name> (LANDING, RAW, TRANSFORM, ANALYTICS, ML)
Warehouse: <your-warehouse>
Role: <your-role>
```

---

## Notes for Tableau Developers

1. **Use ANALYTICS schema tables** for most dashboards - these are pre-aggregated and optimized
2. **Use RAW schema tables** for detailed analysis or when you need to join with other tables
3. **Use ML schema tables** for forecasting and predictive analytics
4. **AGENCY column** is available in most tables - use for filtering BART vs VTA
5. **All timestamps** are in UTC - convert to local timezone (America/Los_Angeles) in Tableau
6. **DELAY_SECONDS** - negative values mean early, positive means late
7. **ON_TIME_PCT** and **RELIABILITY_SCORE** are 0-100 scale
8. **Incremental updates** - Most analytics tables are incrementally updated, so data is always fresh

---

## Sample Queries for Tableau

### Get Route Performance:
```sql
SELECT 
    ROUTE_SHORT_NAME,
    ROUTE_LONG_NAME,
    AGENCY,
    TOTAL_DEPARTURES,
    ON_TIME_PERFORMANCE,
    AVG_DELAY_SECONDS
FROM USER_DB_HORNET.ANALYTICS.ROUTE_PERFORMANCE
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
FROM USER_DB_HORNET.ANALYTICS.RELIABILITY_METRICS
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
FROM USER_DB_HORNET.ML.DEMAND_FORECAST
WHERE FORECAST_DATE >= CURRENT_DATE()
ORDER BY FORECAST_DATE, ROUTE_SHORT_NAME
```

---

**Last Updated**: 2025-01-08
**Contact**: For questions about data structure or availability, contact the data engineering team.

