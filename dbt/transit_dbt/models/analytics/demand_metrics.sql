{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'demand']
  )
}}

{#
  Analytics Mart: Demand Metrics
  
  Calculates demand patterns by stop, route, and time.
  Uses departure frequency as a proxy for demand/service level.
  
  Source: stg_departures, stg_stops, stg_routes
#}

WITH departures AS (
    SELECT 
        stop_id as stop_global_id,
        stop_name,
        route_id as route_global_id,
        route_short_name,
        TO_TIMESTAMP_NTZ(actual_departure_time) as departure_time,
        DATE(TO_TIMESTAMP_NTZ(scheduled_departure_time)) as departure_date,
        HOUR(TO_TIMESTAMP_NTZ(scheduled_departure_time)) as departure_hour,
        DAYOFWEEK(TO_TIMESTAMP_NTZ(scheduled_departure_time)) as departure_day_of_week,
        DAYNAME(TO_TIMESTAMP_NTZ(scheduled_departure_time)) as departure_day_name,
        CASE 
            WHEN delay_seconds IS NULL THEN 'UNKNOWN'
            WHEN delay_seconds <= 0 THEN 'ON_TIME'
            WHEN delay_seconds <= 300 THEN 'LATE'
            ELSE 'VERY_LATE'
        END as delay_status,
        load_timestamp as ingestion_timestamp
    FROM {{ ref('stg_streaming_departures') }}
    {% if is_incremental() %}
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(updated_at), '1900-01-01') FROM {{ this }})
    {% endif %}
),

stops AS (
    SELECT DISTINCT 
        stop_id as stop_global_id, 
        stop_name, 
        stop_lat, 
        stop_lon,
        CAST(location_type AS INTEGER) as location_type,
        parent_station as parent_station_name
    FROM {{ ref('stg_gtfs_stops') }}
),

routes AS (
    SELECT DISTINCT 
        route_id as route_global_id, 
        route_short_name,
        route_long_name,
        agency,
        CAST(route_type AS INTEGER) as route_type
    FROM {{ ref('stg_gtfs_routes') }}
),

-- Calculate departures by stop, route, date, and hour
hourly_departures AS (
    SELECT
        d.stop_global_id,
        d.stop_name,
        d.route_global_id,
        d.route_short_name,
        d.departure_date,
        d.departure_hour,
        d.departure_day_of_week,
        d.departure_day_name,
        COUNT(*) AS departure_count,
        -- Peak period classification
        CASE
            WHEN d.departure_hour BETWEEN 7 AND 9 THEN 'AM_PEAK'
            WHEN d.departure_hour BETWEEN 16 AND 19 THEN 'PM_PEAK'
            WHEN d.departure_hour BETWEEN 10 AND 15 THEN 'MIDDAY'
            WHEN d.departure_hour BETWEEN 20 AND 23 THEN 'EVENING'
            ELSE 'OVERNIGHT'
        END AS time_period,
        MAX(d.ingestion_timestamp) AS last_update
    FROM departures d
    WHERE d.stop_global_id IS NOT NULL
      AND d.route_global_id IS NOT NULL
    GROUP BY 
        d.stop_global_id, d.stop_name, d.route_global_id, d.route_short_name,
        d.departure_date, d.departure_hour, d.departure_day_of_week, d.departure_day_name
),

-- Aggregate to daily level with period breakdowns
daily_demand AS (
    SELECT
        stop_global_id,
        stop_name,
        route_global_id,
        route_short_name,
        departure_date,
        departure_day_of_week,
        departure_day_name,
        SUM(departure_count) AS total_departures,
        SUM(CASE WHEN time_period = 'AM_PEAK' THEN departure_count ELSE 0 END) AS am_peak_departures,
        SUM(CASE WHEN time_period = 'PM_PEAK' THEN departure_count ELSE 0 END) AS pm_peak_departures,
        SUM(CASE WHEN time_period = 'MIDDAY' THEN departure_count ELSE 0 END) AS midday_departures,
        SUM(CASE WHEN time_period = 'EVENING' THEN departure_count ELSE 0 END) AS evening_departures,
        SUM(CASE WHEN time_period = 'OVERNIGHT' THEN departure_count ELSE 0 END) AS overnight_departures,
        AVG(departure_count) AS avg_hourly_departures,
        MAX(departure_count) AS max_hourly_departures,
        MAX(last_update) AS last_update
    FROM hourly_departures
    GROUP BY 
        stop_global_id, stop_name, route_global_id, route_short_name,
        departure_date, departure_day_of_week, departure_day_name
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['dd.stop_global_id', 'dd.route_global_id', 'dd.departure_date']) }} AS id,
    
    -- Stop info
    dd.stop_global_id,
    dd.stop_name,
    s.stop_lat,
    s.stop_lon,
    s.location_type,
    s.parent_station_name,
    
    -- Route info
    dd.route_global_id,
    dd.route_short_name,
    r.route_long_name,
    r.agency,
    r.route_type,
    
    -- Date info
    dd.departure_date,
    dd.departure_day_of_week,
    dd.departure_day_name,
    
    -- Departure counts
    dd.total_departures,
    dd.am_peak_departures,
    dd.pm_peak_departures,
    dd.midday_departures,
    dd.evening_departures,
    dd.overnight_departures,
    
    -- Averages
    ROUND(dd.avg_hourly_departures, 2) AS avg_hourly_departures,
    dd.max_hourly_departures,
    
    -- Peak ratio (peak vs total)
    ROUND((dd.am_peak_departures + dd.pm_peak_departures) * 100.0 / NULLIF(dd.total_departures, 0), 2) AS peak_pct,
    
    -- Demand intensity score (0-100)
    CASE
        WHEN dd.total_departures >= 100 THEN 100
        WHEN dd.total_departures >= 50 THEN 80
        WHEN dd.total_departures >= 20 THEN 60
        WHEN dd.total_departures >= 10 THEN 40
        WHEN dd.total_departures >= 5 THEN 20
        ELSE 10
    END AS demand_intensity_score,
    
    dd.last_update,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at

FROM daily_demand dd
LEFT JOIN stops s ON dd.stop_global_id = s.stop_global_id
LEFT JOIN routes r ON dd.route_global_id = r.route_global_id
