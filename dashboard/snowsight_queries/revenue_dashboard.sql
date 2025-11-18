-- Snowsight Dashboard Queries: Revenue Overlay Panel

-- =============================================================================
-- 1. Revenue by Route (Last 7 Days)
-- =============================================================================
SELECT
    route_id,
    SUM(estimated_revenue) AS total_revenue,
    SUM(estimated_ridership) AS total_ridership,
    SUM(revenue_loss_delays) AS total_revenue_loss,
    SUM(revenue_opportunity) AS total_revenue_opportunity,
    AVG(on_time_performance_pct) AS avg_on_time_pct
FROM ANALYTICS.REVENUE_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY route_id
ORDER BY total_revenue DESC;

-- =============================================================================
-- 2. Reliability Impact on Revenue
-- =============================================================================
SELECT
    CASE
        WHEN on_time_performance_pct >= 95 THEN '95-100%'
        WHEN on_time_performance_pct >= 90 THEN '90-95%'
        WHEN on_time_performance_pct >= 80 THEN '80-90%'
        WHEN on_time_performance_pct >= 70 THEN '70-80%'
        ELSE '<70%'
    END AS on_time_performance_bucket,
    COUNT(*) AS route_days,
    AVG(estimated_revenue) AS avg_revenue,
    AVG(revenue_loss_delays) AS avg_revenue_loss,
    AVG(revenue_opportunity) AS avg_revenue_opportunity
FROM ANALYTICS.REVENUE_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY on_time_performance_bucket
ORDER BY on_time_performance_bucket;

-- =============================================================================
-- 3. Top Revenue Loss Routes (Due to Delays)
-- =============================================================================
SELECT
    route_id,
    SUM(revenue_loss_delays) AS total_revenue_loss,
    AVG(avg_delay_seconds) / 60 AS avg_delay_minutes,
    AVG(on_time_performance_pct) AS avg_on_time_pct,
    SUM(estimated_revenue) AS total_revenue,
    (SUM(revenue_loss_delays) / NULLIF(SUM(estimated_revenue), 0) * 100) AS revenue_loss_pct
FROM ANALYTICS.REVENUE_METRICS rm
LEFT JOIN ANALYTICS.RELIABILITY_METRICS rel
    ON rm.route_id = rel.route_id
    AND rm.departure_date = rel.departure_date
WHERE rm.departure_date >= CURRENT_DATE - 7
GROUP BY rm.route_id
HAVING SUM(revenue_loss_delays) > 100  -- Filter routes with significant loss
ORDER BY total_revenue_loss DESC;

