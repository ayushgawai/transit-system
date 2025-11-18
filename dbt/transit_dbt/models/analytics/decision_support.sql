{{
  config(
    materialized='table',
    schema='analytics',
    tags=['analytics', 'decision-support']
  )
}}

-- Analytics mart: Decision Support Recommendations
-- Provides ranked suggestions for fleet reallocation, frequency adjustments, etc.

WITH reliability AS (
    SELECT * FROM {{ ref('reliability_metrics') }}
),

demand AS (
    SELECT * FROM {{ ref('demand_metrics') }}
),

crowding AS (
    SELECT * FROM {{ ref('crowding_metrics') }}
),

revenue AS (
    SELECT * FROM {{ ref('revenue_metrics') }}
),

-- Aggregate metrics by route (latest 7 days)
route_metrics AS (
    SELECT
        r.route_id,
        AVG(r.on_time_performance_pct) AS avg_on_time_pct,
        AVG(r.avg_delay_seconds) AS avg_delay_seconds,
        AVG(r.reliability_score) AS avg_reliability_score,
        AVG(d.total_departures) AS avg_daily_departures,
        AVG(d.demand_intensity_score) AS avg_demand_intensity,
        AVG(c.avg_occupancy_ratio) AS avg_occupancy_ratio,
        AVG(c.crowding_pct) AS avg_crowding_pct,
        SUM(re.estimated_revenue) AS total_revenue_7d,
        SUM(re.revenue_loss_delays) AS total_revenue_loss_7d
    FROM reliability r
    LEFT JOIN demand d ON r.route_id = d.route_id AND r.departure_date = d.departure_date
    LEFT JOIN crowding c ON r.route_id = c.route_id AND r.departure_date = c.departure_date
    LEFT JOIN revenue re ON r.route_id = re.route_id AND r.departure_date = re.departure_date
    WHERE r.departure_date >= CURRENT_DATE - 7
    GROUP BY r.route_id
),

-- Generate recommendations
recommendations AS (
    SELECT
        route_id,
        avg_on_time_pct,
        avg_delay_seconds,
        avg_reliability_score,
        avg_daily_departures,
        avg_demand_intensity,
        avg_occupancy_ratio,
        avg_crowding_pct,
        total_revenue_7d,
        total_revenue_loss_7d,
        -- Recommendation type and priority
        CASE
            WHEN avg_on_time_pct < 80 AND avg_delay_seconds > 300 THEN 'INCREASE_FREQUENCY'
            WHEN avg_crowding_pct > 30 AND avg_occupancy_ratio > 0.8 THEN 'ADD_CAPACITY'
            WHEN avg_reliability_score < 60 AND avg_demand_intensity > 50 THEN 'FLEET_REALLOCATION'
            WHEN total_revenue_loss_7d > 1000 THEN 'IMPROVE_RELIABILITY'
            ELSE 'MONITOR'
        END AS recommendation_type,
        -- Priority score (higher is more urgent)
        CASE
            WHEN avg_on_time_pct < 80 AND avg_delay_seconds > 300 THEN 90
            WHEN avg_crowding_pct > 30 AND avg_occupancy_ratio > 0.8 THEN 85
            WHEN avg_reliability_score < 60 AND avg_demand_intensity > 50 THEN 80
            WHEN total_revenue_loss_7d > 1000 THEN 75
            ELSE 30
        END AS priority_score,
        -- Recommendation description
        CASE
            WHEN avg_on_time_pct < 80 AND avg_delay_seconds > 300 
            THEN CONCAT('Route has ', ROUND(avg_on_time_pct, 1), '% on-time performance with ', ROUND(avg_delay_seconds/60, 1), ' min avg delay. Consider increasing frequency.')
            WHEN avg_crowding_pct > 30 AND avg_occupancy_ratio > 0.8 
            THEN CONCAT('Route has ', ROUND(avg_crowding_pct, 1), '% crowded departures. Consider adding larger vehicles or increasing frequency.')
            WHEN avg_reliability_score < 60 AND avg_demand_intensity > 50 
            THEN CONCAT('Route has low reliability (', ROUND(avg_reliability_score, 1), ') with high demand. Consider reallocating fleet resources.')
            WHEN total_revenue_loss_7d > 1000 
            THEN CONCAT('Route has lost $', ROUND(total_revenue_loss_7d, 2), ' in revenue due to delays. Focus on improving reliability.')
            ELSE 'Route is performing within acceptable parameters. Continue monitoring.'
        END AS recommendation_description
    FROM route_metrics
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['route_id', 'recommendation_type']) }} AS id,
    route_id,
    avg_on_time_pct,
    avg_delay_seconds,
    avg_reliability_score,
    avg_daily_departures,
    avg_demand_intensity,
    avg_occupancy_ratio,
    avg_crowding_pct,
    total_revenue_7d,
    total_revenue_loss_7d,
    recommendation_type,
    priority_score,
    recommendation_description,
    current_timestamp() AS created_at
FROM recommendations
ORDER BY priority_score DESC, route_id

