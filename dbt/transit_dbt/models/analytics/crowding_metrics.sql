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
        departure_key,
        stop_global_id,
        stop_name,
        route_global_id,
        route_short_name,
        departure_date,
        departure_hour,
        departure_time,
        occupancy_status,
        is_real_time,
        ingestion_timestamp
    FROM {{ ref('stg_departures') }}
    {% if is_incremental() %}
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(updated_at), '1900-01-01') FROM {{ this }})
    {% endif %}
),

-- Map occupancy_status to numeric values (proxy for crowding)
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
        CASE UPPER(COALESCE(occupancy_status, 'UNKNOWN'))
            WHEN 'EMPTY' THEN 0.0
            WHEN 'MANY_SEATS_AVAILABLE' THEN 0.25
            WHEN 'FEW_SEATS_AVAILABLE' THEN 0.50
            WHEN 'STANDING_ROOM_ONLY' THEN 0.75
            WHEN 'CRUSHED_STANDING_ROOM_ONLY' THEN 0.95
            WHEN 'FULL' THEN 1.0
            WHEN 'NOT_ACCEPTING_PASSENGERS' THEN 1.0
            ELSE 0.50  -- Default if unknown
        END AS occupancy_ratio,
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
