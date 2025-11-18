-- Snowsight Dashboard Queries: Decision Support Table

-- =============================================================================
-- 1. Ranked Recommendations by Priority
-- =============================================================================
SELECT
    route_id,
    recommendation_type,
    priority_score,
    recommendation_description,
    avg_on_time_pct,
    avg_delay_seconds / 60 AS avg_delay_minutes,
    avg_reliability_score,
    avg_crowding_pct,
    total_revenue_loss_7d,
    created_at
FROM ANALYTICS.DECISION_SUPPORT
ORDER BY priority_score DESC, route_id
LIMIT 20;

-- =============================================================================
-- 2. Fleet Reallocation Recommendations
-- =============================================================================
SELECT
    route_id,
    avg_reliability_score,
    avg_demand_intensity,
    avg_crowding_pct,
    total_revenue_7d,
    recommendation_description,
    priority_score
FROM ANALYTICS.DECISION_SUPPORT
WHERE recommendation_type = 'FLEET_REALLOCATION'
ORDER BY priority_score DESC;

-- =============================================================================
-- 3. Frequency Increase Recommendations
-- =============================================================================
SELECT
    route_id,
    avg_on_time_pct,
    avg_delay_seconds / 60 AS avg_delay_minutes,
    avg_daily_departures,
    avg_crowding_pct,
    recommendation_description,
    priority_score
FROM ANALYTICS.DECISION_SUPPORT
WHERE recommendation_type = 'INCREASE_FREQUENCY'
ORDER BY priority_score DESC;

-- =============================================================================
-- 4. Capacity Expansion Recommendations
-- =============================================================================
SELECT
    route_id,
    avg_occupancy_ratio,
    avg_crowding_pct,
    avg_daily_departures,
    avg_demand_intensity,
    recommendation_description,
    priority_score
FROM ANALYTICS.DECISION_SUPPORT
WHERE recommendation_type = 'ADD_CAPACITY'
ORDER BY priority_score DESC;

-- =============================================================================
-- 5. Revenue Impact of Recommendations
-- =============================================================================
SELECT
    recommendation_type,
    COUNT(*) AS recommendation_count,
    AVG(priority_score) AS avg_priority_score,
    SUM(total_revenue_7d) AS total_revenue_impact,
    SUM(total_revenue_loss_7d) AS total_revenue_loss,
    AVG(total_revenue_loss_7d) AS avg_revenue_loss_per_route
FROM ANALYTICS.DECISION_SUPPORT
WHERE recommendation_type != 'MONITOR'
GROUP BY recommendation_type
ORDER BY avg_priority_score DESC;

