-- ============================================================================
-- TRANSIT SYSTEM - LANDING TABLES (Source/Raw Layer)
-- ============================================================================
-- These are the ONLY tables created with raw SQL.
-- All transformations happen in dbt.
-- 
-- These tables are APPEND-ONLY - new data is always inserted, never truncated.
-- This preserves history for analytics and streaming use cases.
-- ============================================================================

USE DATABASE USER_DB_HORNET;
USE SCHEMA RAW;

-- ============================================================================
-- 1. RAW DEPARTURES - Real-time departure data from TransitApp API
-- ============================================================================
-- This is the primary streaming table - new departures append every 5 minutes
-- Used for: Real-time headway analysis, delay detection, on-time performance

CREATE TABLE IF NOT EXISTS RAW.TRANSIT_DEPARTURES (
    -- Metadata columns
    ingestion_id STRING DEFAULT UUID_STRING(),           -- Unique ID for each ingestion batch
    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),  -- When data was loaded
    source_file STRING,                                   -- S3 path or local file path
    api_endpoint STRING DEFAULT 'stop_departures',        -- API endpoint used
    
    -- Raw JSON payload (entire API response)
    raw_json VARIANT,
    
    -- Extracted keys for partitioning/querying (denormalized for performance)
    stop_global_id STRING,                                -- Extracted from raw_json for filtering
    stop_name STRING,                                     -- Extracted for readability
    fetch_timestamp TIMESTAMP_NTZ,                        -- When API was called
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Clustering for query performance
    CLUSTER BY (DATE(ingestion_timestamp), stop_global_id)
);

-- ============================================================================
-- 2. RAW STOPS - Stop/station reference data from TransitApp API
-- ============================================================================
-- Semi-static data - refreshed periodically
-- Used for: Stop dimension, geographic analysis, route mapping

CREATE TABLE IF NOT EXISTS RAW.TRANSIT_STOPS (
    -- Metadata columns
    ingestion_id STRING DEFAULT UUID_STRING(),
    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file STRING,
    api_endpoint STRING DEFAULT 'nearby_stops',
    
    -- Raw JSON payload
    raw_json VARIANT,
    
    -- Extracted keys
    location_lat FLOAT,                                   -- Query location latitude
    location_lon FLOAT,                                   -- Query location longitude
    stops_count INT,                                      -- Number of stops in response
    fetch_timestamp TIMESTAMP_NTZ,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- 3. RAW ALERTS - Service alerts and disruptions
-- ============================================================================
-- Streaming data - alerts come and go
-- Used for: Disruption analysis, impact assessment

CREATE TABLE IF NOT EXISTS RAW.TRANSIT_ALERTS (
    -- Metadata columns
    ingestion_id STRING DEFAULT UUID_STRING(),
    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file STRING,
    api_endpoint STRING DEFAULT 'alerts',
    
    -- Raw JSON payload
    raw_json VARIANT,
    
    -- Extracted keys
    alert_count INT,
    fetch_timestamp TIMESTAMP_NTZ,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- 4. RAW GTFS - Static GTFS feed metadata
-- ============================================================================
-- Static data - refreshed daily/weekly
-- Used for: Scheduled times, route definitions, calendar

CREATE TABLE IF NOT EXISTS RAW.TRANSIT_GTFS_FEEDS (
    -- Metadata columns
    ingestion_id STRING DEFAULT UUID_STRING(),
    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file STRING,                                   -- S3 path to zip file
    
    -- Feed info
    agency STRING,                                        -- BART, Caltrain, etc.
    feed_url STRING,                                      -- Original download URL
    file_size_bytes INT,
    
    -- Parsed GTFS tables (stored as arrays of objects)
    gtfs_routes VARIANT,                                  -- routes.txt parsed
    gtfs_stops VARIANT,                                   -- stops.txt parsed
    gtfs_trips VARIANT,                                   -- trips.txt parsed
    gtfs_stop_times VARIANT,                              -- stop_times.txt parsed
    gtfs_calendar VARIANT,                                -- calendar.txt parsed
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- 5. RAW ROUTES - Route information extracted from departures
-- ============================================================================
-- Derived from departure data - routes seen in the system
-- Used for: Route dimension, route-level metrics

CREATE TABLE IF NOT EXISTS RAW.TRANSIT_ROUTES (
    -- Metadata columns
    ingestion_id STRING DEFAULT UUID_STRING(),
    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file STRING,
    
    -- Raw JSON payload
    raw_json VARIANT,
    
    -- Extracted keys
    global_route_id STRING,
    route_name STRING,
    route_type INT,
    agency STRING,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- 6. SNOWFLAKE STREAM - For CDC (Change Data Capture) on Departures
-- ============================================================================
-- This stream captures all new inserts to TRANSIT_DEPARTURES
-- Used by: Dynamic Tables, incremental dbt models, Kafka connector

CREATE STREAM IF NOT EXISTS RAW.TRANSIT_DEPARTURES_STREAM
    ON TABLE RAW.TRANSIT_DEPARTURES
    APPEND_ONLY = TRUE                                    -- Only track inserts (not updates/deletes)
    SHOW_INITIAL_ROWS = FALSE;                            -- Don't include existing rows

-- ============================================================================
-- GRANTS - Ensure roles can access these tables
-- ============================================================================
-- Adjust role name if different

GRANT SELECT ON ALL TABLES IN SCHEMA RAW TO ROLE TRAINING_ROLE;
GRANT SELECT ON ALL STREAMS IN SCHEMA RAW TO ROLE TRAINING_ROLE;
GRANT INSERT ON ALL TABLES IN SCHEMA RAW TO ROLE TRAINING_ROLE;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after creating tables to verify:

-- SHOW TABLES IN SCHEMA RAW LIKE 'TRANSIT%';
-- SHOW STREAMS IN SCHEMA RAW LIKE 'TRANSIT%';
-- DESCRIBE TABLE RAW.TRANSIT_DEPARTURES;

-- ============================================================================
-- END OF LANDING TABLES
-- ============================================================================
-- Next step: Update dbt models in dbt/transit_dbt/models/staging/ 
-- to read from these landing tables
-- ============================================================================

