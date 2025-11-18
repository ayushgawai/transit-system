-- Snowsight Dashboard Queries: Demand & Crowding Heatmap

-- =============================================================================
-- 1. Boarding Heatmap by Stop and Hour (Last 7 Days)
-- =============================================================================
SELECT
    stop_id,
    stop_name,
    departure_hour,
    SUM(total_departures) AS total_boardings,  -- Proxy for actual boardings
    AVG(demand_intensity_score) AS avg_demand_intensity
FROM ANALYTICS.DEMAND_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY stop_id, stop_name, departure_hour
ORDER BY total_boardings DESC, departure_hour;

-- =============================================================================
-- 2. Top Routes by Total Demand (Last 7 Days)
-- =============================================================================
SELECT
    route_id,
    route_short_name,
    route_long_name,
    SUM(total_departures) AS total_departures,
    AVG(demand_intensity_score) AS avg_demand_intensity,
    SUM(morning_peak_departures) AS morning_peak,
    SUM(evening_peak_departures) AS evening_peak
FROM ANALYTICS.DEMAND_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY route_id, route_short_name, route_long_name
ORDER BY total_departures DESC
LIMIT 20;

-- =============================================================================
-- 3. Crowding by Route and Hour (Last 7 Days)
-- =============================================================================
SELECT
    route_id,
    departure_hour,
    AVG(avg_occupancy_ratio) AS avg_occupancy,
    AVG(crowding_pct) AS crowding_percentage,
    SUM(crowded_departures) AS total_crowded_departures,
    AVG(capacity_utilization_score) AS capacity_utilization
FROM ANALYTICS.CROWDING_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY route_id, departure_hour
ORDER BY crowding_percentage DESC;

-- =============================================================================
-- 4. Peak vs Off-Peak Demand Comparison
-- =============================================================================
SELECT
    route_id,
    AVG(morning_peak_departures) AS avg_morning_peak,
    AVG(evening_peak_departures) AS avg_evening_peak,
    AVG(midday_departures) AS avg_midday,
    AVG(off_peak_departures) AS avg_off_peak,
    (AVG(morning_peak_departures) + AVG(evening_peak_departures)) / 
    NULLIF(AVG(midday_departures) + AVG(off_peak_departures), 0) AS peak_to_off_peak_ratio
FROM ANALYTICS.DEMAND_METRICS
WHERE departure_date >= CURRENT_DATE - 7
GROUP BY route_id
ORDER BY peak_to_off_peak_ratio DESC;

