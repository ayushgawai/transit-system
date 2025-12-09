{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'crowding']
  )
}}

{#
  Analytics Mart: Crowding Metrics
  
  Estimates vehicle occupancy and capacity utilization.
  Uses occupancy_status from real-time data when available.
  
  Source: stg_departures
#}

WITH departures AS (
    SELECT 
        id as departure_key,
        stop_id as stop_global_id,
        stop_name,
        route_id as route_global_id,
        route_short_name,
        DATE(TO_TIMESTAMP_NTZ(scheduled_departure_time)) as departure_date,
        HOUR(TO_TIMESTAMP_NTZ(scheduled_departure_time)) as departure_hour,
        TO_TIMESTAMP_NTZ(actual_departure_time) as departure_time,
        delay_seconds,
        is_real_time,
        load_timestamp as ingestion_timestamp,
        -- Estimate occupancy based on delay and time of day (proxy since we don't have actual occupancy)
        CASE 
            WHEN HOUR(TO_TIMESTAMP_NTZ(scheduled_departure_time)) BETWEEN 7 AND 9 THEN 0.75  -- AM peak
            WHEN HOUR(TO_TIMESTAMP_NTZ(scheduled_departure_time)) BETWEEN 17 AND 19 THEN 0.80  -- PM peak
            WHEN delay_seconds > 300 THEN 0.85  -- High delay suggests crowding
            ELSE 0.50  -- Off-peak default
        END AS occupancy_ratio
    FROM {{ ref('stg_streaming_departures') }}
    WHERE scheduled_departure_time IS NOT NULL
    {% if is_incremental() %}
    AND load_timestamp > (SELECT COALESCE(MAX(updated_at), '1900-01-01') FROM {{ this }})
    {% endif %}
),

-- Map occupancy to standardized values (proxy since we don't have actual occupancy data)
occupancy_mapping AS (
    SELECT
        departure_key,
        stop_global_id,
        route_global_id,
        route_short_name,
        departure_date,
        departure_hour,
        departure_time,
        is_real_time,
        occupancy_ratio,
        ingestion_timestamp
    FROM departures
),

crowding_by_route_hour AS (
    SELECT
        route_global_id,
        route_short_name,
        departure_date,
        departure_hour,
        COUNT(*) AS total_departures,
        SUM(CASE WHEN is_real_time THEN 1 ELSE 0 END) AS realtime_departures,
        AVG(occupancy_ratio) AS avg_occupancy_ratio,
        MEDIAN(occupancy_ratio) AS median_occupancy_ratio,
        MAX(occupancy_ratio) AS max_occupancy_ratio,
        SUM(CASE WHEN occupancy_ratio >= 0.9 THEN 1 ELSE 0 END) AS crowded_count,
        SUM(CASE WHEN occupancy_ratio >= 0.75 THEN 1 ELSE 0 END) AS near_capacity_count,
        SUM(CASE WHEN occupancy_ratio <= 0.25 THEN 1 ELSE 0 END) AS low_occupancy_count,
        MAX(ingestion_timestamp) AS last_update
    FROM occupancy_mapping
    GROUP BY route_global_id, route_short_name, departure_date, departure_hour
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['route_global_id', 'departure_date', 'departure_hour']) }} AS id,
    
    route_global_id,
    route_short_name,
    departure_date,
    departure_hour,
    total_departures,
    realtime_departures,
    
    -- Occupancy metrics
    ROUND(avg_occupancy_ratio, 4) AS avg_occupancy_ratio,
    ROUND(median_occupancy_ratio, 4) AS median_occupancy_ratio,
    ROUND(max_occupancy_ratio, 4) AS max_occupancy_ratio,
    
    -- Crowding counts
    crowded_count,
    near_capacity_count,
    low_occupancy_count,
    
    -- Percentages
    ROUND(crowded_count * 100.0 / NULLIF(total_departures, 0), 2) AS crowded_pct,
    ROUND(near_capacity_count * 100.0 / NULLIF(total_departures, 0), 2) AS near_capacity_pct,
    ROUND(low_occupancy_count * 100.0 / NULLIF(total_departures, 0), 2) AS low_occupancy_pct,
    
    -- Capacity utilization score (0-100, higher is more utilized/crowded)
    ROUND(avg_occupancy_ratio * 100, 2) AS capacity_utilization_score,
    
    -- Real-time data coverage
    ROUND(realtime_departures * 100.0 / NULLIF(total_departures, 0), 2) AS realtime_pct,
    
    last_update,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at

FROM crowding_by_route_hour
