{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'crowding']
  )
}}

-- Analytics mart: Crowding Metrics
-- Estimates vehicle occupancy and capacity utilization using occupancy_status from departures

WITH departures AS (
    SELECT * FROM {{ ref('stg_departures') }}
    {% if is_incremental() %}
    WHERE load_timestamp > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}
),

-- Map occupancy_status to numeric values (proxy for crowding)
occupancy_mapping AS (
    SELECT
        departure_id,
        stop_id,
        route_id,
        departure_date,
        departure_hour,
        departure_time,
        CASE occupancy_status
            WHEN 'EMPTY' THEN 0.0
            WHEN 'MANY_SEATS_AVAILABLE' THEN 0.25
            WHEN 'FEW_SEATS_AVAILABLE' THEN 0.75
            WHEN 'STANDING_ROOM_ONLY' THEN 0.95
            WHEN 'CRUSHED_STANDING_ROOM_ONLY' THEN 1.0
            WHEN 'FULL' THEN 1.0
            ELSE 0.5  -- Default if unknown
        END AS occupancy_ratio
    FROM departures
    WHERE occupancy_status IS NOT NULL
),

crowding_by_route_hour AS (
    SELECT
        route_id,
        departure_date,
        departure_hour,
        COUNT(*) AS total_departures,
        AVG(occupancy_ratio) AS avg_occupancy_ratio,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY occupancy_ratio) AS p75_occupancy_ratio,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY occupancy_ratio) AS p95_occupancy_ratio,
        SUM(CASE WHEN occupancy_ratio >= 0.9 THEN 1 ELSE 0 END) AS crowded_departures,
        SUM(CASE WHEN occupancy_ratio >= 0.75 THEN 1 ELSE 0 END) AS near_capacity_departures
    FROM occupancy_mapping
    GROUP BY route_id, departure_date, departure_hour
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['route_id', 'departure_date', 'departure_hour']) }} AS id,
    route_id,
    departure_date,
    departure_hour,
    total_departures,
    avg_occupancy_ratio,
    p75_occupancy_ratio,
    p95_occupancy_ratio,
    crowded_departures,
    near_capacity_departures,
    -- Crowding percentage
    CASE
        WHEN total_departures > 0
        THEN (crowded_departures::FLOAT / total_departures * 100)
        ELSE NULL
    END AS crowding_pct,
    -- Capacity utilization score (0-100, higher is more crowded)
    ROUND(avg_occupancy_ratio * 100, 2) AS capacity_utilization_score,
    current_timestamp() AS created_at,
    current_timestamp() AS updated_at
FROM crowding_by_route_hour

