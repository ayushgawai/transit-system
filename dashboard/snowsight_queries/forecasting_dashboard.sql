-- Snowsight Dashboard Queries: Forecasting Panel

-- =============================================================================
-- 1. Next 24h Demand Forecast
-- =============================================================================
SELECT
    route_id,
    stop_id,
    forecast_timestamp,
    predicted_value AS predicted_boardings,
    confidence_interval_lower,
    confidence_interval_upper,
    model_version
FROM ML.FORECASTS
WHERE forecast_type = 'demand'
  AND forecast_timestamp >= CURRENT_TIMESTAMP()
  AND forecast_timestamp <= CURRENT_TIMESTAMP() + INTERVAL '24 hours'
ORDER BY forecast_timestamp, predicted_value DESC;

-- =============================================================================
-- 2. Demand Forecast vs Historical Average (by Route)
-- =============================================================================
WITH forecast_agg AS (
    SELECT
        route_id,
        DATE_TRUNC('hour', forecast_timestamp) AS forecast_hour,
        AVG(predicted_value) AS avg_predicted_boardings
    FROM ML.FORECASTS
    WHERE forecast_type = 'demand'
      AND forecast_timestamp >= CURRENT_TIMESTAMP()
    GROUP BY route_id, forecast_hour
),
historical_avg AS (
    SELECT
        route_id,
        departure_hour,
        AVG(total_departures) AS avg_historical_boardings
    FROM ANALYTICS.DEMAND_METRICS
    WHERE departure_date >= CURRENT_DATE - 30
    GROUP BY route_id, departure_hour
)
SELECT
    f.route_id,
    f.forecast_hour,
    f.avg_predicted_boardings,
    h.avg_historical_boardings,
    (f.avg_predicted_boardings - h.avg_historical_boardings) AS forecast_delta,
    ((f.avg_predicted_boardings - h.avg_historical_boardings) / NULLIF(h.avg_historical_boardings, 0) * 100) AS forecast_delta_pct
FROM forecast_agg f
LEFT JOIN historical_avg h
    ON f.route_id = h.route_id
    AND EXTRACT(HOUR FROM f.forecast_hour) = h.departure_hour
ORDER BY forecast_delta_pct DESC;

-- =============================================================================
-- 3. Delay Forecast (Next 48 Hours)
-- =============================================================================
SELECT
    route_id,
    stop_id,
    forecast_timestamp,
    predicted_value AS predicted_delay_seconds,
    predicted_value / 60 AS predicted_delay_minutes,
    confidence_interval_lower / 60 AS ci_lower_minutes,
    confidence_interval_upper / 60 AS ci_upper_minutes
FROM ML.FORECASTS
WHERE forecast_type = 'delay'
  AND forecast_timestamp >= CURRENT_TIMESTAMP()
  AND forecast_timestamp <= CURRENT_TIMESTAMP() + INTERVAL '48 hours'
ORDER BY forecast_timestamp, predicted_value DESC;

-- =============================================================================
-- 4. Crowding Forecast (Next 24 Hours)
-- =============================================================================
SELECT
    route_id,
    forecast_timestamp,
    predicted_value AS predicted_occupancy_ratio,
    CASE
        WHEN predicted_value >= 0.9 THEN 'CRUSHED'
        WHEN predicted_value >= 0.75 THEN 'STANDING'
        WHEN predicted_value >= 0.5 THEN 'FEW_SEATS'
        ELSE 'MANY_SEATS'
    END AS predicted_crowding_status,
    confidence_interval_lower,
    confidence_interval_upper
FROM ML.FORECASTS
WHERE forecast_type = 'crowding'
  AND forecast_timestamp >= CURRENT_TIMESTAMP()
  AND forecast_timestamp <= CURRENT_TIMESTAMP() + INTERVAL '24 hours'
ORDER BY predicted_occupancy_ratio DESC;

