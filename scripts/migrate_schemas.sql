-- ============================================================================
-- SCHEMA MIGRATION SCRIPT
-- ============================================================================
-- This script creates proper schemas and migrates tables to correct locations
-- 
-- Schema Structure:
--   LANDING  - Raw data from APIs/GTFS (initial ingestion)
--   RAW      - Cleaned raw data (from dbt staging models)
--   STAGING  - Staging views/models (dbt staging)
--   TRANSFORM - Intermediate transformations (dbt transform)
--   ANALYTICS - Final analytics tables (dbt analytics)
--   ML       - ML models and forecasts (dbt ml_forecasts)
-- ============================================================================

-- Step 1: Create all schemas
CREATE SCHEMA IF NOT EXISTS LANDING;
CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS STAGING;
CREATE SCHEMA IF NOT EXISTS TRANSFORM;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;
CREATE SCHEMA IF NOT EXISTS ML;

-- Step 2: Backup existing tables (create backup schema)
CREATE SCHEMA IF NOT EXISTS BACKUP_20250108;

-- Step 3: Move LANDING tables from ANALYTICS to LANDING schema
-- (These will be created by the migration script, but we document them here)

-- Tables that should be in LANDING:
--   LANDING_GTFS_STOPS
--   LANDING_GTFS_ROUTES
--   LANDING_GTFS_TRIPS
--   LANDING_GTFS_STOP_TIMES
--   LANDING_STREAMING_DEPARTURES
--   GTFS_LOAD_HISTORY

-- Step 4: Tables that should be in RAW (from dbt staging models):
--   STG_GTFS_STOPS
--   STG_GTFS_ROUTES
--   STG_GTFS_TRIPS
--   STG_GTFS_STOP_TIMES
--   STG_STREAMING_DEPARTURES

-- Step 5: Tables that should be in TRANSFORM:
--   (Intermediate transformation tables)

-- Step 6: Tables that should be in ANALYTICS:
--   RELIABILITY_METRICS
--   DEMAND_METRICS
--   CROWDING_METRICS
--   REVENUE_METRICS
--   DECISION_SUPPORT
--   ROUTE_PERFORMANCE

-- Step 7: Tables that should be in ML:
--   DEMAND_FORECAST
--   DELAY_FORECAST

