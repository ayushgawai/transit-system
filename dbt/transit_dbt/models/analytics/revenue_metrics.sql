{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'revenue']
  )
}}

-- Analytics mart: Revenue Metrics
-- Links service reliability & ridership to financial impact
-- Note: Actual fare revenue data may need to come from additional sources
-- This uses departures as a proxy for ridership, then estimates revenue

WITH departures AS (
    SELECT * FROM {{ ref('stg_departures') }}
    {% if is_incremental() %}
    WHERE load_timestamp > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}
),

reliability AS (
    SELECT * FROM {{ ref('reliability_metrics') }}
),

demand AS (
    SELECT * FROM {{ ref('demand_metrics') }}
),

-- Estimate ridership from departure counts (proxy: assume ~30 passengers per departure on average)
-- In production, use actual fare collection data
estimated_ridership AS (
    SELECT
        route_id,
        departure_date,
        SUM(total_departures) AS total_departures,
        SUM(total_departures) * 30 AS estimated_ridership  -- Proxy: 30 passengers per departure
    FROM demand
    GROUP BY route_id, departure_date
),

-- Estimate revenue (proxy: assume $2.50 average fare)
estimated_revenue AS (
    SELECT
        route_id,
        departure_date,
        total_departures,
        estimated_ridership,
        estimated_ridership * 2.50 AS estimated_revenue
    FROM estimated_ridership
),

-- Combine with reliability metrics
revenue_with_reliability AS (
    SELECT
        er.route_id,
        er.departure_date,
        er.total_departures,
        er.estimated_ridership,
        er.estimated_revenue,
        r.on_time_performance_pct,
        r.avg_delay_seconds,
        r.reliability_score,
        -- Revenue impact of delays (estimate: 5% ridership loss per 10-minute delay)
        er.estimated_revenue * (1 - (GREATEST(0, r.avg_delay_seconds / 600) * 0.05)) AS revenue_after_delay_impact,
        -- Potential revenue if on-time performance were 95%
        CASE
            WHEN r.on_time_performance_pct < 95
            THEN er.estimated_revenue * (1 + ((95 - r.on_time_performance_pct) / 100) * 0.10)
            ELSE er.estimated_revenue
        END AS potential_revenue_high_reliability
    FROM estimated_revenue er
    LEFT JOIN (
        SELECT
            route_id,
            departure_date,
            AVG(on_time_performance_pct) AS on_time_performance_pct,
            AVG(avg_delay_seconds) AS avg_delay_seconds,
            AVG(reliability_score) AS reliability_score
        FROM reliability
        GROUP BY route_id, departure_date
    ) r ON er.route_id = r.route_id AND er.departure_date = r.departure_date
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['route_id', 'departure_date']) }} AS id,
    route_id,
    departure_date,
    total_departures,
    estimated_ridership,
    estimated_revenue,
    on_time_performance_pct,
    avg_delay_seconds,
    reliability_score,
    revenue_after_delay_impact,
    potential_revenue_high_reliability,
    -- Revenue loss due to delays
    estimated_revenue - revenue_after_delay_impact AS revenue_loss_delays,
    -- Revenue opportunity from improving reliability
    potential_revenue_high_reliability - estimated_revenue AS revenue_opportunity,
    current_timestamp() AS created_at,
    current_timestamp() AS updated_at
FROM revenue_with_reliability

