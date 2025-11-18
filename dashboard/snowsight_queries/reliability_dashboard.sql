-- Snowsight Dashboard Queries: Service Reliability Monitor
-- Use these queries to build visualizations in Snowsight

-- =============================================================================
-- 1. On-Time Performance by Route (Last 7 Days)
-- =============================================================================
SELECT
    route_id,
    AVG(on_time_performance_pct) AS avg_on_time_pct,
    AVG(avg_delay_seconds) / 60 AS avg_delay_minutes,
    SUM(total_departures) AS total_departures,
    AVG(reliability_score) AS avg_reliability_score
FROM ANALYTICS.RELIABILITY_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY route_id
ORDER BY avg_on_time_pct DESC;

-- =============================================================================
-- 2. Headway Consistency by Route
-- =============================================================================
SELECT
    route_id,
    AVG(avg_headway_seconds) / 60 AS avg_headway_minutes,
    AVG(median_headway_seconds) / 60 AS median_headway_minutes,
    AVG(headway_cv) AS avg_headway_cv,  -- Lower is better (more consistent)
    AVG(reliability_score) AS reliability_score
FROM ANALYTICS.RELIABILITY_METRICS
WHERE departure_date >= CURRENT_DATE - 7
  AND headway_count > 0
GROUP BY route_id
ORDER BY avg_headway_cv ASC;

-- =============================================================================
-- 3. Delay Distribution by Hour of Day
-- =============================================================================
SELECT
    departure_hour,
    AVG(avg_delay_seconds) / 60 AS avg_delay_minutes,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_delay_seconds) / 60 AS median_delay_minutes,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY avg_delay_seconds) / 60 AS p95_delay_minutes,
    COUNT(*) AS data_points
FROM ANALYTICS.RELIABILITY_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY departure_hour
ORDER BY departure_hour;

-- =============================================================================
-- 4. Service Alerts Impact (Last 7 Days)
-- =============================================================================
SELECT
    route_id,
    COUNT(*) AS alert_count,
    SUM(duration_minutes) AS total_alert_duration_minutes,
    AVG(duration_minutes) AS avg_alert_duration_minutes,
    MAX(duration_minutes) AS max_alert_duration_minutes
FROM STAGING.STG_ALERTS
WHERE start_time >= CURRENT_DATE - 7
  AND is_active = TRUE
GROUP BY route_id
ORDER BY alert_count DESC;

