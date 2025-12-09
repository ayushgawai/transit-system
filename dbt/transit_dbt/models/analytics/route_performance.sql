-- Analytics model: Route Performance Metrics
{{ config(
    materialized='table',
    schema='ANALYTICS'
) }}

WITH route_base AS (
    SELECT DISTINCT
        route_id,
        agency,
        route_short_name,
        route_long_name
    FROM {{ ref('stg_gtfs_routes') }}
),
route_departure_agg AS (
    SELECT
        route_id,
        agency,
        COUNT(DISTINCT trip_id) as total_trips,
        COUNT(DISTINCT stop_id) as total_stops,
        COUNT(*) as total_departures
    FROM {{ ref('route_departures') }}
    GROUP BY route_id, agency
),
route_stats AS (
    SELECT
        r.route_id,
        r.agency,
        r.route_short_name,
        r.route_long_name,
        COALESCE(rd.total_trips, 0) as total_trips,
        COALESCE(rd.total_stops, 0) as total_stops,
        COALESCE(rd.total_departures, 0) as total_departures
    FROM route_base r
    LEFT JOIN route_departure_agg rd ON r.route_id = rd.route_id AND r.agency = rd.agency
),
streaming_stats AS (
    SELECT
        route_id,
        COALESCE(agency, 'UNKNOWN') as agency,
        COUNT(*) as streaming_departures,
        AVG(CASE WHEN delay_seconds > 0 THEN delay_seconds ELSE NULL END) as avg_delay_seconds,
        SUM(CASE WHEN delay_seconds BETWEEN -300 AND 300 THEN 1 ELSE 0 END) as on_time_count
    FROM {{ ref('stg_streaming_departures') }}
    WHERE is_real_time = true
    GROUP BY route_id, COALESCE(agency, 'UNKNOWN')
)
SELECT
    rs.route_id,
    rs.agency,
    rs.route_short_name,
    rs.route_long_name,
    rs.total_trips,
    rs.total_stops,
    rs.total_departures,
    COALESCE(ss.streaming_departures, 0) as streaming_departures,
    COALESCE(ss.avg_delay_seconds, 0) as avg_delay_seconds,
    CASE 
        WHEN ss.streaming_departures > 0 
        THEN (ss.on_time_count::FLOAT / ss.streaming_departures * 100)
        ELSE 100.0
    END as on_time_performance,
    CURRENT_TIMESTAMP as updated_at
FROM route_stats rs
LEFT JOIN streaming_stats ss ON rs.route_id = ss.route_id AND rs.agency = ss.agency
WHERE rs.agency IS NOT NULL
