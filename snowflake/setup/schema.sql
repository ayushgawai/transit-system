-- Snowflake Database and Schema Setup
-- Run this script to create the database, schemas, and initial tables

-- =============================================================================
-- DATABASE AND SCHEMAS
-- =============================================================================

CREATE DATABASE IF NOT EXISTS TRANSIT_DB;
USE DATABASE TRANSIT_DB;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS STAGING;
CREATE SCHEMA IF NOT EXISTS TRANSFORM;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;
CREATE SCHEMA IF NOT EXISTS ML;

-- =============================================================================
-- RAW SCHEMA: Landing tables for Snowpipe
-- =============================================================================

USE SCHEMA RAW;

-- TransitApp API calls (JSON dumps)
CREATE TABLE IF NOT EXISTS TRANSITAPP_API_CALLS (
    value VARIANT,
    metadata VARIANT,
    metadata$filename STRING,
    metadata$file_row_number INTEGER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- GTFS Routes (from routes.txt)
CREATE TABLE IF NOT EXISTS GTFS_ROUTES (
    value STRING,
    metadata VARIANT,
    metadata$filename STRING,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- GTFS Stops (from stops.txt)
CREATE TABLE IF NOT EXISTS GTFS_STOPS (
    value STRING,
    metadata VARIANT,
    metadata$filename STRING,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- GTFS Trips (from trips.txt)
CREATE TABLE IF NOT EXISTS GTFS_TRIPS (
    value STRING,
    metadata VARIANT,
    metadata$filename STRING,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- GTFS Stop Times (from stop_times.txt)
CREATE TABLE IF NOT EXISTS GTFS_STOP_TIMES (
    value STRING,
    metadata VARIANT,
    metadata$filename STRING,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- STAGING SCHEMA: Cleaned data (populated by dbt)
-- =============================================================================

USE SCHEMA STAGING;

-- Staging tables are created as views by dbt, but we can create placeholder tables if needed
-- dbt will create: stg_departures, stg_alerts, stg_routes, stg_stops, stg_trips

-- =============================================================================
-- TRANSFORM SCHEMA: Transformed data (populated by dbt)
-- =============================================================================

USE SCHEMA TRANSFORM;

-- Transform tables are created as tables by dbt for intermediate transformations

-- =============================================================================
-- ANALYTICS SCHEMA: Analytics tables (populated by dbt)
-- =============================================================================

USE SCHEMA ANALYTICS;

-- Analytics marts are created as tables by dbt
-- dbt will create: reliability_metrics, demand_metrics, crowding_metrics, revenue_metrics, decision_support, forecasts

-- =============================================================================
-- ML SCHEMA: ML models and predictions
-- =============================================================================

USE SCHEMA ML;

-- Forecasts table (populated by ML models)
CREATE TABLE IF NOT EXISTS FORECASTS (
    id STRING PRIMARY KEY,
    forecast_type STRING,  -- 'demand', 'delay', 'crowding'
    route_id STRING,
    stop_id STRING,
    forecast_timestamp TIMESTAMP_NTZ,
    predicted_value FLOAT,
    confidence_interval_lower FLOAT,
    confidence_interval_upper FLOAT,
    model_version STRING,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Model metadata table
CREATE TABLE IF NOT EXISTS MODEL_METADATA (
    model_id STRING PRIMARY KEY,
    model_type STRING,
    model_version STRING,
    training_date DATE,
    training_data_range_start DATE,
    training_data_range_end DATE,
    model_metrics VARIANT,  -- JSON with accuracy metrics
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- WAREHOUSE SETUP
-- =============================================================================

CREATE WAREHOUSE IF NOT EXISTS TRANSIT_WH
    WITH WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60  -- Auto-suspend after 60 seconds of inactivity
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;  -- Start suspended to save credits

-- =============================================================================
-- ROLES AND PERMISSIONS
-- =============================================================================

-- Create role for data ingestion (Snowpipe, Lambda)
CREATE ROLE IF NOT EXISTS TRANSIT_INGESTION_ROLE;

-- Create role for dbt transformations
CREATE ROLE IF NOT EXISTS TRANSIT_ROLE;
GRANT ROLE TRANSIT_ROLE TO ROLE TRANSIT_INGESTION_ROLE;

-- Grant permissions
GRANT USAGE ON WAREHOUSE TRANSIT_WH TO ROLE TRANSIT_ROLE;
GRANT USAGE ON DATABASE TRANSIT_DB TO ROLE TRANSIT_ROLE;
GRANT USAGE ON SCHEMA RAW TO ROLE TRANSIT_INGESTION_ROLE;
GRANT INSERT ON SCHEMA RAW TO ROLE TRANSIT_INGESTION_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA RAW TO ROLE TRANSIT_INGESTION_ROLE;

GRANT USAGE ON SCHEMA STAGING TO ROLE TRANSIT_ROLE;
GRANT SELECT, INSERT, UPDATE ON SCHEMA STAGING TO ROLE TRANSIT_ROLE;

GRANT USAGE ON SCHEMA TRANSFORM TO ROLE TRANSIT_ROLE;
GRANT SELECT, INSERT, UPDATE ON SCHEMA TRANSFORM TO ROLE TRANSIT_ROLE;

GRANT USAGE ON SCHEMA ANALYTICS TO ROLE TRANSIT_ROLE;
GRANT SELECT, INSERT, UPDATE ON SCHEMA ANALYTICS TO ROLE TRANSIT_ROLE;

GRANT USAGE ON SCHEMA ML TO ROLE TRANSIT_ROLE;
GRANT SELECT, INSERT, UPDATE ON SCHEMA ML TO ROLE TRANSIT_ROLE;

