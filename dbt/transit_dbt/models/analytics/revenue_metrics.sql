{{
  config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    schema='analytics',
    tags=['analytics', 'revenue']
  )
}}

{#
  Analytics Mart: Revenue Metrics
  
  Links service reliability & ridership to estimated financial impact.
  Uses fare data from routes and departure counts as proxies.
  
  Note: For actual revenue, integrate fare collection data.
  
  Sources: stg_departures, stg_routes, reliability_metrics, demand_metrics
#}

WITH departures AS (
    SELECT 
        route_global_id,
        route_short_name,
        departure_date,
        COUNT(*) AS departure_count,
        MAX(ingestion_timestamp) AS last_update
    FROM {{ ref('stg_departures') }}
    {% if is_incremental() %}
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(updated_at), '1900-01-01') FROM {{ this }})
    {% endif %}
    GROUP BY route_global_id, route_short_name, departure_date
),

routes AS (
    SELECT DISTINCT
        route_global_id,
        route_short_name,
        min_fare,
        max_fare,
        fare_currency
    FROM {{ ref('stg_routes') }}
),

reliability AS (
    SELECT 
        route_global_id,
        departure_date,
        AVG(on_time_pct) AS on_time_pct,
        AVG(avg_delay_seconds) AS avg_delay_seconds,
        AVG(reliability_score) AS reliability_score
    FROM {{ ref('reliability_metrics') }}
    GROUP BY route_global_id, departure_date
),

-- Estimate ridership and revenue
-- Assumptions (can be adjusted):
-- - Average 25 passengers per departure
-- - Use route's avg fare or default $2.50
estimated_metrics AS (
    SELECT
        d.route_global_id,
        d.route_short_name,
        d.departure_date,
        d.departure_count,
        
        -- Estimated ridership (25 passengers per departure avg)
        d.departure_count * 25 AS estimated_ridership,
        
        -- Use fare from routes or default $2.50
        COALESCE((r.min_fare + r.max_fare) / 2, 2.50) AS avg_fare,
        
        -- Estimated revenue
        d.departure_count * 25 * COALESCE((r.min_fare + r.max_fare) / 2, 2.50) AS estimated_revenue,
        
        -- Reliability metrics
        rel.on_time_pct,
        rel.avg_delay_seconds,
        rel.reliability_score,
        
        d.last_update
    FROM departures d
    LEFT JOIN routes r ON d.route_global_id = r.route_global_id
    LEFT JOIN reliability rel ON d.route_global_id = rel.route_global_id AND d.departure_date = rel.departure_date
),

-- Calculate revenue impact
revenue_impact AS (
    SELECT
        *,
        -- Revenue impact from delays
        -- Assumption: 3% ridership loss per 5-minute avg delay
        CASE 
            WHEN avg_delay_seconds > 0 
            THEN estimated_revenue * (1 - LEAST((avg_delay_seconds / 300) * 0.03, 0.20))  -- Cap at 20% loss
            ELSE estimated_revenue
        END AS revenue_after_delays,
        
        -- Potential revenue if reliability were 95%+
        CASE
            WHEN on_time_pct < 95 
            THEN estimated_revenue * (1 + ((95 - COALESCE(on_time_pct, 85)) / 100) * 0.08)
            ELSE estimated_revenue
        END AS potential_revenue_95_pct
    FROM estimated_metrics
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['route_global_id', 'departure_date']) }} AS id,
    
    route_global_id,
    route_short_name,
    departure_date,
    departure_count,
    
    -- Ridership & Revenue
    estimated_ridership,
    ROUND(avg_fare, 2) AS avg_fare,
    ROUND(estimated_revenue, 2) AS estimated_revenue,
    
    -- Reliability
    ROUND(on_time_pct, 2) AS on_time_pct,
    ROUND(avg_delay_seconds, 2) AS avg_delay_seconds,
    ROUND(reliability_score, 2) AS reliability_score,
    
    -- Revenue Impact
    ROUND(revenue_after_delays, 2) AS revenue_after_delays,
    ROUND(estimated_revenue - revenue_after_delays, 2) AS revenue_loss_delays,
    ROUND(potential_revenue_95_pct, 2) AS potential_revenue_95_pct,
    ROUND(potential_revenue_95_pct - estimated_revenue, 2) AS revenue_opportunity,
    
    -- Revenue per departure (efficiency metric)
    ROUND(estimated_revenue / NULLIF(departure_count, 0), 2) AS revenue_per_departure,
    
    last_update,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at

FROM revenue_impact
