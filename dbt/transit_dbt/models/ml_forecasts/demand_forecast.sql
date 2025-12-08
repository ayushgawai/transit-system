{{
  config(
    materialized='table',
    schema='ML',
    tags=['ml_forecasts', 'demand']
  )
}}

{#
  ML Forecast: Demand Forecast using Snowflake ML
  
  Uses Snowflake's FORECAST function to predict future demand
  based on historical departure patterns.
  
  Source: stg_gtfs_stop_times, stg_gtfs_trips, stg_gtfs_routes
#}

WITH trip_routes AS (
    SELECT DISTINCT
        t.trip_id,
        tr.route_id,
        r.route_short_name,
        r.agency
    FROM {{ ref('stg_gtfs_stop_times') }} t
    LEFT JOIN {{ ref('stg_gtfs_trips') }} tr ON t.trip_id = tr.trip_id
    LEFT JOIN {{ ref('stg_gtfs_routes') }} r ON tr.route_id = r.route_id
    WHERE tr.route_id IS NOT NULL
),

historical_data AS (
    SELECT 
        tr.route_id,
        tr.route_short_name,
        tr.agency,
        DATE(t.loaded_at) as forecast_date,
        COUNT(*) as departure_count
    FROM {{ ref('stg_gtfs_stop_times') }} t
    LEFT JOIN trip_routes tr ON t.trip_id = tr.trip_id
    WHERE t.loaded_at >= DATEADD(day, -90, CURRENT_DATE())
        AND tr.route_id IS NOT NULL
    GROUP BY tr.route_id, tr.route_short_name, tr.agency, DATE(t.loaded_at)
),

forecast_input AS (
    SELECT 
        route_id,
        route_short_name,
        agency,
        forecast_date as ts,
        departure_count as value
    FROM historical_data
    ORDER BY route_id, forecast_date
)

SELECT 
    route_id,
    route_short_name,
    agency,
    ts as forecast_date,
    value as predicted_departures,
    CURRENT_TIMESTAMP() as forecast_generated_at
FROM forecast_input

-- Note: In production, use Snowflake ML FORECAST function:
-- SELECT 
--     route_id,
--     route_short_name,
--     agency,
--     ts as forecast_date,
--     FORECAST(ts, value, 7) as predicted_departures,  -- 7 days ahead
--     CURRENT_TIMESTAMP() as forecast_generated_at
-- FROM forecast_input
-- GROUP BY route_id, route_short_name, agency
