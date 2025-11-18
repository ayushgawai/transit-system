{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'reliability']
  )
}}

-- Analytics mart: Service Reliability Metrics
-- Calculates on-time performance, headway gaps, service consistency by route/stop/time

WITH departures AS (
    SELECT * FROM {{ ref('stg_departures') }}
    {% if is_incremental() %}
    WHERE load_timestamp > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}
),

routes AS (
    SELECT DISTINCT route_id FROM {{ ref('stg_routes') }}
),

-- Calculate on-time performance by route and hour
on_time_performance AS (
    SELECT
        route_id,
        departure_date,
        departure_hour,
        COUNT(*) AS total_departures,
        SUM(CASE WHEN delay_status = 'ON_TIME' THEN 1 ELSE 0 END) AS on_time_departures,
        SUM(CASE WHEN delay_status = 'LATE' THEN 1 ELSE 0 END) AS late_departures,
        SUM(CASE WHEN delay_status = 'VERY_LATE' THEN 1 ELSE 0 END) AS very_late_departures,
        AVG(delay_seconds) AS avg_delay_seconds,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_seconds) AS median_delay_seconds,
        STDDEV(delay_seconds) AS stddev_delay_seconds
    FROM departures
    WHERE route_id IS NOT NULL
    GROUP BY route_id, departure_date, departure_hour
),

-- Calculate headway gaps (time between consecutive departures at same stop)
headway_gaps AS (
    SELECT
        d1.stop_id,
        d1.route_id,
        d1.departure_time,
        d1.departure_date,
        d1.departure_hour,
        MIN(d2.departure_time) AS next_departure_time,
        DATEDIFF(SECOND, d1.departure_time, MIN(d2.departure_time)) AS headway_seconds
    FROM departures d1
    LEFT JOIN departures d2
        ON d1.stop_id = d2.stop_id
        AND d1.route_id = d2.route_id
        AND d2.departure_time > d1.departure_time
        AND d2.departure_date = d1.departure_date
    WHERE d1.stop_id IS NOT NULL
    GROUP BY d1.stop_id, d1.route_id, d1.departure_time, d1.departure_date, d1.departure_hour
    HAVING headway_seconds IS NOT NULL
),

headway_metrics AS (
    SELECT
        route_id,
        departure_date,
        departure_hour,
        COUNT(*) AS headway_count,
        AVG(headway_seconds) AS avg_headway_seconds,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY headway_seconds) AS median_headway_seconds,
        STDDEV(headway_seconds) AS stddev_headway_seconds,
        -- Coefficient of variation (measure of consistency)
        STDDEV(headway_seconds) / NULLIF(AVG(headway_seconds), 0) AS headway_cv
    FROM headway_gaps
    WHERE headway_seconds > 0  -- Filter out invalid headways
    GROUP BY route_id, departure_date, departure_hour
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['otp.route_id', 'otp.departure_date', 'otp.departure_hour']) }} AS id,
    otp.route_id,
    otp.departure_date,
    otp.departure_hour,
    otp.total_departures,
    otp.on_time_departures,
    otp.late_departures,
    otp.very_late_departures,
    -- On-time performance percentage
    CASE
        WHEN otp.total_departures > 0
        THEN (otp.on_time_departures::FLOAT / otp.total_departures * 100)
        ELSE NULL
    END AS on_time_performance_pct,
    otp.avg_delay_seconds,
    otp.median_delay_seconds,
    otp.stddev_delay_seconds,
    -- Headway metrics
    hm.headway_count,
    hm.avg_headway_seconds,
    hm.median_headway_seconds,
    hm.stddev_headway_seconds,
    hm.headway_cv,
    -- Reliability score (composite metric: 0-100, higher is better)
    CASE
        WHEN otp.total_departures >= 5  -- Minimum sample size
        THEN (
            (otp.on_time_departures::FLOAT / otp.total_departures * 50) +  -- 50% weight on on-time performance
            (CASE WHEN otp.avg_delay_seconds < 0 THEN 25 ELSE GREATEST(0, 25 - (otp.avg_delay_seconds / 60 * 25)) END) +  -- 25% weight on delay
            (CASE WHEN hm.headway_cv < 0.3 THEN 25 ELSE GREATEST(0, 25 - ((hm.headway_cv - 0.3) * 50)) END)  -- 25% weight on consistency
        )
        ELSE NULL
    END AS reliability_score,
    current_timestamp() AS created_at,
    current_timestamp() AS updated_at
FROM on_time_performance otp
LEFT JOIN headway_metrics hm
    ON otp.route_id = hm.route_id
    AND otp.departure_date = hm.departure_date
    AND otp.departure_hour = hm.departure_hour

