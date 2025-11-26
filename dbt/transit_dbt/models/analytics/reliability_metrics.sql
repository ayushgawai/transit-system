{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'reliability']
  )
}}

{#
  Analytics Mart: Service Reliability Metrics
  
  Calculates:
  - On-time performance by route/hour
  - Headway gaps (time between consecutive departures)
  - Service consistency metrics
  - Composite reliability score
  
  Source: stg_departures (staging)
#}

WITH departures AS (
    SELECT 
        departure_key,
        stop_global_id,
        stop_name,
        route_global_id,
        route_short_name,
        direction_headsign,
        departure_time,
        scheduled_departure_time,
        delay_seconds,
        delay_status,
        is_real_time,
        departure_date,
        departure_hour,
        departure_day_of_week,
        ingestion_timestamp
    FROM {{ ref('stg_departures') }}
    {% if is_incremental() %}
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(updated_at), '1900-01-01') FROM {{ this }})
    {% endif %}
),

-- Calculate on-time performance by route and hour
on_time_performance AS (
    SELECT
        route_global_id,
        route_short_name,
        departure_date,
        departure_hour,
        COUNT(*) AS total_departures,
        SUM(CASE WHEN delay_status = 'ON_TIME' THEN 1 ELSE 0 END) AS on_time_departures,
        SUM(CASE WHEN delay_status = 'EARLY' THEN 1 ELSE 0 END) AS early_departures,
        SUM(CASE WHEN delay_status = 'LATE' THEN 1 ELSE 0 END) AS late_departures,
        SUM(CASE WHEN delay_status = 'VERY_LATE' THEN 1 ELSE 0 END) AS very_late_departures,
        AVG(delay_seconds) AS avg_delay_seconds,
        MEDIAN(delay_seconds) AS median_delay_seconds,
        STDDEV(delay_seconds) AS stddev_delay_seconds,
        MAX(ingestion_timestamp) AS last_update
    FROM departures
    WHERE route_global_id IS NOT NULL
    GROUP BY route_global_id, route_short_name, departure_date, departure_hour
),

-- Calculate headway gaps (time between consecutive departures at same stop/route)
headway_calc AS (
    SELECT
        stop_global_id,
        route_global_id,
        departure_date,
        departure_hour,
        departure_time,
        LAG(departure_time) OVER (
            PARTITION BY stop_global_id, route_global_id, direction_headsign
            ORDER BY departure_time
        ) AS prev_departure_time
    FROM departures
    WHERE departure_time IS NOT NULL
),

headway_gaps AS (
    SELECT
        route_global_id,
        departure_date,
        departure_hour,
        TIMESTAMPDIFF('second', prev_departure_time, departure_time) AS headway_seconds
    FROM headway_calc
    WHERE prev_departure_time IS NOT NULL
      AND departure_time > prev_departure_time
      AND TIMESTAMPDIFF('second', prev_departure_time, departure_time) BETWEEN 60 AND 7200  -- 1 min to 2 hours
),

headway_metrics AS (
    SELECT
        route_global_id,
        departure_date,
        departure_hour,
        COUNT(*) AS headway_count,
        AVG(headway_seconds) AS avg_headway_seconds,
        MEDIAN(headway_seconds) AS median_headway_seconds,
        STDDEV(headway_seconds) AS stddev_headway_seconds,
        -- Coefficient of variation (measure of consistency)
        CASE 
            WHEN AVG(headway_seconds) > 0 
            THEN STDDEV(headway_seconds) / AVG(headway_seconds)
            ELSE NULL 
        END AS headway_cv
    FROM headway_gaps
    GROUP BY route_global_id, departure_date, departure_hour
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['otp.route_global_id', 'otp.departure_date', 'otp.departure_hour']) }} AS id,
    otp.route_global_id,
    otp.route_short_name,
    otp.departure_date,
    otp.departure_hour,
    otp.total_departures,
    otp.on_time_departures,
    otp.early_departures,
    otp.late_departures,
    otp.very_late_departures,
    
    -- On-time performance percentage
    ROUND(otp.on_time_departures * 100.0 / NULLIF(otp.total_departures, 0), 2) AS on_time_pct,
    
    -- Delay metrics
    ROUND(otp.avg_delay_seconds, 2) AS avg_delay_seconds,
    ROUND(otp.median_delay_seconds, 2) AS median_delay_seconds,
    ROUND(otp.stddev_delay_seconds, 2) AS stddev_delay_seconds,
    
    -- Headway metrics
    COALESCE(hm.headway_count, 0) AS headway_count,
    ROUND(hm.avg_headway_seconds / 60.0, 2) AS avg_headway_minutes,
    ROUND(hm.median_headway_seconds / 60.0, 2) AS median_headway_minutes,
    ROUND(hm.headway_cv, 4) AS headway_cv,
    
    -- Reliability score (0-100, higher is better)
    CASE
        WHEN otp.total_departures >= 3 THEN
            ROUND(
                -- 50% weight on on-time performance
                (otp.on_time_departures * 50.0 / NULLIF(otp.total_departures, 0)) +
                -- 30% weight on delay (less delay = better)
                GREATEST(0, 30 - COALESCE(otp.avg_delay_seconds / 60.0, 0) * 3) +
                -- 20% weight on consistency (lower CV = better)
                CASE 
                    WHEN hm.headway_cv IS NULL THEN 10  -- Partial credit if no headway data
                    WHEN hm.headway_cv < 0.3 THEN 20
                    WHEN hm.headway_cv < 0.5 THEN 15
                    WHEN hm.headway_cv < 0.7 THEN 10
                    ELSE 5
                END
            , 2)
        ELSE NULL
    END AS reliability_score,
    
    otp.last_update,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at

FROM on_time_performance otp
LEFT JOIN headway_metrics hm
    ON otp.route_global_id = hm.route_global_id
    AND otp.departure_date = hm.departure_date
    AND otp.departure_hour = hm.departure_hour
