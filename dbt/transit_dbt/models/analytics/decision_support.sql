{{
  config(
    materialized='table',
    schema='analytics',
    tags=['analytics', 'decision-support']
  )
}}

{#
  Analytics Mart: Decision Support Recommendations
  
  Provides AI-style ranked suggestions for:
  - Fleet reallocation
  - Frequency adjustments
  - Capacity improvements
  - Reliability focus areas
  
  Sources: reliability_metrics, demand_metrics, crowding_metrics, revenue_metrics
#}

WITH reliability AS (
    SELECT 
        route_global_id,
        route_short_name,
        departure_date,
        on_time_pct,
        avg_delay_seconds,
        reliability_score,
        avg_headway_minutes
    FROM {{ ref('reliability_metrics') }}
),

demand AS (
    SELECT 
        route_global_id,
        departure_date,
        total_departures,
        demand_intensity_score,
        peak_pct
    FROM {{ ref('demand_metrics') }}
),

crowding AS (
    SELECT 
        route_global_id,
        departure_date,
        avg_occupancy_ratio,
        crowded_pct,
        capacity_utilization_score
    FROM {{ ref('crowding_metrics') }}
),

revenue AS (
    SELECT 
        route_global_id,
        departure_date,
        estimated_revenue,
        revenue_loss_delays,
        revenue_opportunity
    FROM {{ ref('revenue_metrics') }}
),

-- Aggregate metrics by route (most recent data)
route_summary AS (
    SELECT
        r.route_global_id,
        r.route_short_name,
        
        -- Reliability metrics
        AVG(r.on_time_pct) AS avg_on_time_pct,
        AVG(r.avg_delay_seconds) AS avg_delay_seconds,
        AVG(r.reliability_score) AS avg_reliability_score,
        AVG(r.avg_headway_minutes) AS avg_headway_minutes,
        
        -- Demand metrics
        AVG(d.total_departures) AS avg_daily_departures,
        AVG(d.demand_intensity_score) AS avg_demand_intensity,
        AVG(d.peak_pct) AS avg_peak_pct,
        
        -- Crowding metrics
        AVG(c.avg_occupancy_ratio) AS avg_occupancy_ratio,
        AVG(c.crowded_pct) AS avg_crowded_pct,
        AVG(c.capacity_utilization_score) AS avg_capacity_utilization,
        
        -- Revenue metrics
        SUM(COALESCE(rev.estimated_revenue, 0)) AS total_revenue,
        SUM(COALESCE(rev.revenue_loss_delays, 0)) AS total_revenue_loss,
        SUM(COALESCE(rev.revenue_opportunity, 0)) AS total_revenue_opportunity,
        
        MAX(r.departure_date) AS last_data_date
        
    FROM reliability r
    LEFT JOIN demand d ON r.route_global_id = d.route_global_id AND r.departure_date = d.departure_date
    LEFT JOIN crowding c ON r.route_global_id = c.route_global_id AND r.departure_date = c.departure_date
    LEFT JOIN revenue rev ON r.route_global_id = rev.route_global_id AND r.departure_date = rev.departure_date
    GROUP BY r.route_global_id, r.route_short_name
),

-- Generate AI-style recommendations
recommendations AS (
    SELECT
        route_global_id,
        route_short_name,
        avg_on_time_pct,
        avg_delay_seconds,
        avg_reliability_score,
        avg_headway_minutes,
        avg_daily_departures,
        avg_demand_intensity,
        avg_peak_pct,
        avg_occupancy_ratio,
        avg_crowded_pct,
        avg_capacity_utilization,
        total_revenue,
        total_revenue_loss,
        total_revenue_opportunity,
        last_data_date,
        
        -- Recommendation Type
        CASE
            WHEN avg_crowded_pct > 20 AND avg_capacity_utilization > 70 THEN 'ADD_BUSES'
            WHEN avg_on_time_pct < 85 AND avg_delay_seconds > 180 THEN 'IMPROVE_RELIABILITY'
            WHEN avg_capacity_utilization < 30 AND avg_demand_intensity < 30 THEN 'REDUCE_FREQUENCY'
            WHEN avg_reliability_score < 70 AND avg_demand_intensity > 60 THEN 'FLEET_REALLOCATION'
            WHEN total_revenue_loss > total_revenue * 0.05 THEN 'REVENUE_RECOVERY'
            WHEN avg_headway_minutes > 15 AND avg_demand_intensity > 50 THEN 'INCREASE_FREQUENCY'
            ELSE 'MONITOR'
        END AS recommendation_type,
        
        -- Priority Score (0-100, higher = more urgent)
        CASE
            WHEN avg_crowded_pct > 20 AND avg_capacity_utilization > 70 THEN 95
            WHEN avg_on_time_pct < 85 AND avg_delay_seconds > 180 THEN 90
            WHEN avg_reliability_score < 70 AND avg_demand_intensity > 60 THEN 85
            WHEN total_revenue_loss > total_revenue * 0.05 THEN 80
            WHEN avg_headway_minutes > 15 AND avg_demand_intensity > 50 THEN 75
            WHEN avg_capacity_utilization < 30 THEN 50
            ELSE 30
        END AS priority_score,
        
        -- Action Description
        CASE
            WHEN avg_crowded_pct > 20 AND avg_capacity_utilization > 70 
            THEN CONCAT('🚌 ADD CAPACITY: Route ', route_short_name, ' has ', ROUND(avg_crowded_pct, 1), '% crowded departures. Add 1-2 buses during peak hours.')
            
            WHEN avg_on_time_pct < 85 AND avg_delay_seconds > 180 
            THEN CONCAT('⏱️ RELIABILITY ALERT: Route ', route_short_name, ' has only ', ROUND(avg_on_time_pct, 1), '% on-time. Avg delay: ', ROUND(avg_delay_seconds/60, 1), ' min. Investigate causes.')
            
            WHEN avg_capacity_utilization < 30 AND avg_demand_intensity < 30 
            THEN CONCAT('📉 UNDERUTILIZED: Route ', route_short_name, ' running at ', ROUND(avg_capacity_utilization, 1), '% capacity. Consider reducing frequency by 20-30%.')
            
            WHEN avg_reliability_score < 70 AND avg_demand_intensity > 60 
            THEN CONCAT('🔄 REALLOCATION NEEDED: Route ', route_short_name, ' has high demand but low reliability (', ROUND(avg_reliability_score, 1), '). Reallocate fleet resources.')
            
            WHEN total_revenue_loss > 0 
            THEN CONCAT('💰 REVENUE IMPACT: Route ', route_short_name, ' losing ~$', ROUND(total_revenue_loss, 0), ' due to delays. Improvement could recover $', ROUND(total_revenue_opportunity, 0), '.')
            
            WHEN avg_headway_minutes > 15 AND avg_demand_intensity > 50 
            THEN CONCAT('⬆️ INCREASE FREQUENCY: Route ', route_short_name, ' has ', ROUND(avg_headway_minutes, 1), ' min headway with high demand. Consider adding trips.')
            
            ELSE CONCAT('✅ MONITOR: Route ', route_short_name, ' is performing within normal parameters. Reliability: ', ROUND(avg_reliability_score, 1), '/100.')
        END AS recommendation_description,
        
        -- Impact Score (estimated benefit of taking action)
        CASE
            WHEN avg_crowded_pct > 20 THEN ROUND(avg_crowded_pct * 2, 0)
            WHEN avg_on_time_pct < 85 THEN ROUND((100 - avg_on_time_pct) * 2, 0)
            WHEN avg_capacity_utilization < 30 THEN ROUND((50 - avg_capacity_utilization), 0)
            ELSE 20
        END AS impact_score
        
    FROM route_summary
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['route_global_id', 'recommendation_type']) }} AS id,
    
    route_global_id,
    route_short_name,
    
    -- Metrics
    ROUND(avg_on_time_pct, 2) AS on_time_pct,
    ROUND(avg_delay_seconds / 60.0, 2) AS avg_delay_minutes,
    ROUND(avg_reliability_score, 2) AS reliability_score,
    ROUND(avg_headway_minutes, 2) AS avg_headway_minutes,
    ROUND(avg_daily_departures, 0) AS avg_daily_departures,
    ROUND(avg_demand_intensity, 2) AS demand_intensity,
    ROUND(avg_capacity_utilization, 2) AS capacity_utilization,
    ROUND(avg_crowded_pct, 2) AS crowded_pct,
    
    -- Revenue
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(total_revenue_loss, 2) AS revenue_loss,
    ROUND(total_revenue_opportunity, 2) AS revenue_opportunity,
    
    -- Recommendation
    recommendation_type,
    priority_score,
    impact_score,
    recommendation_description,
    
    last_data_date,
    CURRENT_TIMESTAMP() AS generated_at

FROM recommendations
WHERE recommendation_type != 'MONITOR' OR priority_score >= 30
ORDER BY priority_score DESC, impact_score DESC
