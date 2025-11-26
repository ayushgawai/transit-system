-- ============================================================================
-- TRANSIT SYSTEM - DYNAMIC TABLES (Streaming Alternative)
-- ============================================================================
-- Dynamic Tables provide near real-time data transformation in Snowflake.
-- They auto-refresh when source data changes.
--
-- Use these as:
-- 1. Backup to Kafka (simpler, no external infrastructure)
-- 2. Real-time aggregations for dashboards
-- 3. Showcase streaming concepts without Kafka complexity
--
-- COST CONTROL:
-- - Dynamic Tables consume credits while refreshing
-- - Use ALTER ... SUSPEND to pause when not needed
-- - Use ALTER ... RESUME to restart
-- ============================================================================

USE DATABASE USER_DB_HORNET;

-- ============================================================================
-- 1. LIVE DEPARTURES - Parsed departure data (streaming!)
-- ============================================================================
-- This replaces the staging view with a Dynamic Table that auto-refreshes.
-- TARGET_LAG = '1 minute' means data is at most 1 minute stale.

CREATE OR REPLACE DYNAMIC TABLE STAGING.LIVE_DEPARTURES
    TARGET_LAG = '1 minute'
    WAREHOUSE = HORNET_QUERY_WH
AS
WITH flattened AS (
    SELECT
        ingestion_timestamp,
        source_file,
        fetch_timestamp,
        -- Stop info
        raw_json:stop:global_stop_id::STRING AS stop_global_id,
        raw_json:stop:stop_name::STRING AS stop_name,
        raw_json:stop:stop_lat::FLOAT AS stop_lat,
        raw_json:stop:stop_lon::FLOAT AS stop_lon,
        -- Route info
        rd.value:global_route_id::STRING AS route_global_id,
        rd.value:route_short_name::STRING AS route_short_name,
        -- Itinerary info
        it.value:direction_headsign::STRING AS direction_headsign,
        -- Schedule items
        si.value:departure_time::INT AS departure_time_unix,
        si.value:scheduled_departure_time::INT AS scheduled_departure_unix,
        si.value:is_real_time::BOOLEAN AS is_real_time,
        si.value:is_cancelled::BOOLEAN AS is_cancelled,
        si.value:trip_id::STRING AS trip_id
    FROM RAW.TRANSIT_DEPARTURES,
    LATERAL FLATTEN(input => raw_json:departures:route_departures, OUTER => TRUE) rd,
    LATERAL FLATTEN(input => rd.value:itineraries, OUTER => TRUE) it,
    LATERAL FLATTEN(input => it.value:schedule_items, OUTER => TRUE) si
    WHERE raw_json IS NOT NULL
      AND si.value:departure_time IS NOT NULL
)
SELECT
    stop_global_id,
    stop_name,
    stop_lat,
    stop_lon,
    route_global_id,
    route_short_name,
    direction_headsign,
    TO_TIMESTAMP_NTZ(departure_time_unix) AS departure_time,
    TO_TIMESTAMP_NTZ(scheduled_departure_unix) AS scheduled_departure_time,
    departure_time_unix - scheduled_departure_unix AS delay_seconds,
    CASE
        WHEN departure_time_unix - COALESCE(scheduled_departure_unix, departure_time_unix) < -60 THEN 'EARLY'
        WHEN departure_time_unix - COALESCE(scheduled_departure_unix, departure_time_unix) <= 300 THEN 'ON_TIME'
        WHEN departure_time_unix - COALESCE(scheduled_departure_unix, departure_time_unix) <= 600 THEN 'LATE'
        ELSE 'VERY_LATE'
    END AS delay_status,
    is_real_time,
    is_cancelled,
    trip_id,
    ingestion_timestamp,
    source_file
FROM flattened
WHERE departure_time_unix > EXTRACT(EPOCH FROM DATEADD(hour, -6, CURRENT_TIMESTAMP()));  -- Only recent departures

-- ============================================================================
-- 2. LIVE HEADWAY METRICS - Real-time headway calculations
-- ============================================================================
-- Calculates time between consecutive departures (headway) per route/direction.
-- This is the KEY METRIC for service reliability!

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.LIVE_HEADWAY_METRICS
    TARGET_LAG = '2 minutes'
    WAREHOUSE = HORNET_QUERY_WH
AS
WITH departure_sequence AS (
    SELECT
        stop_global_id,
        stop_name,
        route_global_id,
        route_short_name,
        direction_headsign,
        departure_time,
        delay_status,
        is_real_time,
        -- Get previous departure time for same route/stop/direction
        LAG(departure_time) OVER (
            PARTITION BY stop_global_id, route_global_id, direction_headsign 
            ORDER BY departure_time
        ) AS prev_departure_time,
        ingestion_timestamp
    FROM STAGING.LIVE_DEPARTURES
    WHERE departure_time >= CURRENT_TIMESTAMP()  -- Future departures only
      AND departure_time <= DATEADD(hour, 2, CURRENT_TIMESTAMP())  -- Next 2 hours
      AND is_cancelled = FALSE
)
SELECT
    stop_global_id,
    stop_name,
    route_global_id,
    route_short_name,
    direction_headsign,
    departure_time,
    delay_status,
    is_real_time,
    -- Calculate headway (minutes between departures)
    TIMESTAMPDIFF(minute, prev_departure_time, departure_time) AS headway_minutes,
    -- Flag large gaps
    CASE 
        WHEN TIMESTAMPDIFF(minute, prev_departure_time, departure_time) > 15 THEN TRUE
        ELSE FALSE
    END AS is_large_gap,
    ingestion_timestamp,
    CURRENT_TIMESTAMP() AS calculated_at
FROM departure_sequence
WHERE prev_departure_time IS NOT NULL;

-- ============================================================================
-- 3. LIVE SERVICE SUMMARY - Dashboard-ready summary metrics
-- ============================================================================
-- Aggregated metrics for dashboard cards

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.LIVE_SERVICE_SUMMARY
    TARGET_LAG = '5 minutes'
    WAREHOUSE = HORNET_QUERY_WH
AS
SELECT
    -- Time window
    DATE_TRUNC('hour', CURRENT_TIMESTAMP()) AS summary_hour,
    
    -- Overall metrics
    COUNT(DISTINCT route_global_id) AS active_routes,
    COUNT(DISTINCT stop_global_id) AS active_stops,
    COUNT(*) AS total_upcoming_departures,
    
    -- On-time performance
    COUNT(CASE WHEN delay_status = 'ON_TIME' THEN 1 END) AS on_time_count,
    COUNT(CASE WHEN delay_status IN ('LATE', 'VERY_LATE') THEN 1 END) AS late_count,
    ROUND(
        100.0 * COUNT(CASE WHEN delay_status = 'ON_TIME' THEN 1 END) / NULLIF(COUNT(*), 0), 
        1
    ) AS on_time_percentage,
    
    -- Real-time data coverage
    COUNT(CASE WHEN is_real_time = TRUE THEN 1 END) AS realtime_count,
    ROUND(
        100.0 * COUNT(CASE WHEN is_real_time = TRUE THEN 1 END) / NULLIF(COUNT(*), 0),
        1
    ) AS realtime_percentage,
    
    -- Delay stats
    AVG(delay_seconds) AS avg_delay_seconds,
    MAX(delay_seconds) AS max_delay_seconds,
    
    -- Last update
    MAX(ingestion_timestamp) AS last_data_update,
    CURRENT_TIMESTAMP() AS calculated_at

FROM STAGING.LIVE_DEPARTURES
WHERE departure_time BETWEEN CURRENT_TIMESTAMP() AND DATEADD(hour, 2, CURRENT_TIMESTAMP());

-- ============================================================================
-- 4. ROUTE PERFORMANCE LIVE - Per-route metrics
-- ============================================================================

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.LIVE_ROUTE_PERFORMANCE
    TARGET_LAG = '5 minutes'
    WAREHOUSE = HORNET_QUERY_WH
AS
SELECT
    route_global_id,
    route_short_name,
    
    -- Counts
    COUNT(DISTINCT stop_global_id) AS stops_served,
    COUNT(DISTINCT direction_headsign) AS directions,
    COUNT(*) AS upcoming_departures,
    
    -- On-time performance
    ROUND(
        100.0 * COUNT(CASE WHEN delay_status = 'ON_TIME' THEN 1 END) / NULLIF(COUNT(*), 0),
        1
    ) AS on_time_pct,
    
    -- Delay metrics
    AVG(delay_seconds) AS avg_delay_sec,
    MAX(delay_seconds) AS max_delay_sec,
    
    -- Headway (from headway table)
    -- Will be joined in dashboard queries
    
    CURRENT_TIMESTAMP() AS calculated_at

FROM STAGING.LIVE_DEPARTURES
WHERE departure_time BETWEEN CURRENT_TIMESTAMP() AND DATEADD(hour, 2, CURRENT_TIMESTAMP())
  AND is_cancelled = FALSE
GROUP BY route_global_id, route_short_name;

-- ============================================================================
-- CONTROL COMMANDS (Run manually to control costs)
-- ============================================================================

-- PAUSE all Dynamic Tables (stops refresh, saves credits):
-- ALTER DYNAMIC TABLE STAGING.LIVE_DEPARTURES SUSPEND;
-- ALTER DYNAMIC TABLE ANALYTICS.LIVE_HEADWAY_METRICS SUSPEND;
-- ALTER DYNAMIC TABLE ANALYTICS.LIVE_SERVICE_SUMMARY SUSPEND;
-- ALTER DYNAMIC TABLE ANALYTICS.LIVE_ROUTE_PERFORMANCE SUSPEND;

-- RESUME Dynamic Tables (restart refresh):
-- ALTER DYNAMIC TABLE STAGING.LIVE_DEPARTURES RESUME;
-- ALTER DYNAMIC TABLE ANALYTICS.LIVE_HEADWAY_METRICS RESUME;
-- ALTER DYNAMIC TABLE ANALYTICS.LIVE_SERVICE_SUMMARY RESUME;
-- ALTER DYNAMIC TABLE ANALYTICS.LIVE_ROUTE_PERFORMANCE RESUME;

-- Check status:
-- SHOW DYNAMIC TABLES LIKE 'LIVE%';

-- Check refresh history:
-- SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
-- WHERE NAME LIKE 'LIVE%'
-- ORDER BY REFRESH_START_TIME DESC
-- LIMIT 20;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- After creating, run these to verify:

-- SHOW DYNAMIC TABLES IN SCHEMA STAGING;
-- SHOW DYNAMIC TABLES IN SCHEMA ANALYTICS;
-- SELECT * FROM STAGING.LIVE_DEPARTURES LIMIT 10;
-- SELECT * FROM ANALYTICS.LIVE_SERVICE_SUMMARY;

-- ============================================================================
-- END OF DYNAMIC TABLES
-- ============================================================================

