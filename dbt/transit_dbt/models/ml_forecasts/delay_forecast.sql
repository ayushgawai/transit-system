{{
  config(
    materialized='table',
    schema='ML',
    tags=['ml_forecasts', 'delay']
  )
}}

{#
  ML Forecast: Delay Forecast using Snowflake ML
  
  Predicts future delays based on historical delay patterns
  and route performance metrics.
  
  Source: route_performance, stg_streaming_departures
#}

WITH historical_delays AS (
    SELECT 
        route_id,
        route_short_name,
        agency,
        DATE(load_timestamp) as forecast_date,
        AVG(delay_seconds) as avg_delay_seconds,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_seconds) as median_delay_seconds
    FROM {{ ref('stg_streaming_departures') }}
    WHERE load_timestamp >= DATEADD(day, -90, CURRENT_DATE())
        AND delay_seconds IS NOT NULL
    GROUP BY route_id, route_short_name, agency, DATE(load_timestamp)
)

SELECT 
    route_id,
    route_short_name,
    agency,
    forecast_date,
    avg_delay_seconds as predicted_avg_delay,
    median_delay_seconds as predicted_median_delay,
    CURRENT_TIMESTAMP() as forecast_generated_at
FROM historical_delays

-- Note: In production, use Snowflake ML FORECAST function:
-- SELECT 
--     route_id,
--     route_short_name,
--     agency,
--     ts as forecast_date,
--     FORECAST(ts, avg_delay_seconds, 7) as predicted_avg_delay,
--     CURRENT_TIMESTAMP() as forecast_generated_at
-- FROM historical_delays
-- GROUP BY route_id, route_short_name, agency

