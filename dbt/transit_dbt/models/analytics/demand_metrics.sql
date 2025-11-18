{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'demand']
  )
}}

-- Analytics mart: Demand Metrics
-- Calculates boarding counts, passenger demand by stop/route/time
-- Note: Actual boarding data may need to come from additional sources
-- This uses departures as a proxy for demand

WITH departures AS (
    SELECT * FROM {{ ref('stg_departures') }}
    {% if is_incremental() %}
    WHERE load_timestamp > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}
),

stops AS (
    SELECT DISTINCT stop_id, stop_name, stop_lat, stop_lon FROM {{ ref('stg_stops') }}
),

routes AS (
    SELECT DISTINCT route_id, route_short_name, route_long_name, route_type_name FROM {{ ref('stg_routes') }}
),

-- Calculate departures (proxy for demand) by stop, route, and time
departure_counts AS (
    SELECT
        d.stop_id,
        d.route_id,
        d.departure_date,
        d.departure_hour,
        d.departure_day_of_week,
        COUNT(*) AS departure_count,
        -- Peak vs off-peak classification
        CASE
            WHEN d.departure_hour BETWEEN 7 AND 9 THEN 'MORNING_PEAK'
            WHEN d.departure_hour BETWEEN 17 AND 19 THEN 'EVENING_PEAK'
            WHEN d.departure_hour BETWEEN 10 AND 16 THEN 'MIDDAY'
            ELSE 'OFF_PEAK'
        END AS time_period
    FROM departures d
    WHERE d.stop_id IS NOT NULL
      AND d.route_id IS NOT NULL
    GROUP BY d.stop_id, d.route_id, d.departure_date, d.departure_hour, d.departure_day_of_week
),

-- Aggregate to daily level
daily_demand AS (
    SELECT
        stop_id,
        route_id,
        departure_date,
        departure_day_of_week,
        SUM(departure_count) AS total_departures,
        SUM(CASE WHEN time_period = 'MORNING_PEAK' THEN departure_count ELSE 0 END) AS morning_peak_departures,
        SUM(CASE WHEN time_period = 'EVENING_PEAK' THEN departure_count ELSE 0 END) AS evening_peak_departures,
        SUM(CASE WHEN time_period = 'MIDDAY' THEN departure_count ELSE 0 END) AS midday_departures,
        SUM(CASE WHEN time_period = 'OFF_PEAK' THEN departure_count ELSE 0 END) AS off_peak_departures,
        AVG(departure_count) AS avg_hourly_departures,
        MAX(departure_count) AS max_hourly_departures
    FROM departure_counts
    GROUP BY stop_id, route_id, departure_date, departure_day_of_week
),

-- Calculate demand metrics with route and stop metadata
demand_with_metadata AS (
    SELECT
        dd.stop_id,
        s.stop_name,
        s.stop_lat,
        s.stop_lon,
        dd.route_id,
        r.route_short_name,
        r.route_long_name,
        r.route_type_name,
        dd.departure_date,
        dd.departure_day_of_week,
        dd.total_departures,
        dd.morning_peak_departures,
        dd.evening_peak_departures,
        dd.midday_departures,
        dd.off_peak_departures,
        dd.avg_hourly_departures,
        dd.max_hourly_departures,
        -- Demand intensity score (0-100, higher is busier)
        CASE
            WHEN dd.total_departures >= 50 THEN 100
            WHEN dd.total_departures >= 30 THEN 75
            WHEN dd.total_departures >= 15 THEN 50
            WHEN dd.total_departures >= 5 THEN 25
            ELSE 0
        END AS demand_intensity_score
    FROM daily_demand dd
    LEFT JOIN stops s ON dd.stop_id = s.stop_id
    LEFT JOIN routes r ON dd.route_id = r.route_id
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['stop_id', 'route_id', 'departure_date']) }} AS id,
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    route_id,
    route_short_name,
    route_long_name,
    route_type_name,
    departure_date,
    departure_day_of_week,
    total_departures,
    morning_peak_departures,
    evening_peak_departures,
    midday_departures,
    off_peak_departures,
    avg_hourly_departures,
    max_hourly_departures,
    demand_intensity_score,
    current_timestamp() AS created_at,
    current_timestamp() AS updated_at
FROM demand_with_metadata

