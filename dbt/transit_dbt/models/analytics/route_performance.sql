-- Analytics model: Route Performance Metrics
{{ config(
    materialized='incremental',
    unique_key='route_id||agency',
    incremental_strategy='merge',
    schema='ANALYTICS'
) }}

WITH route_stats AS (
    SELECT
        r.route_id,
        r.agency,
        r.route_short_name,
        r.route_long_name,
        COUNT(DISTINCT rd.trip_id) as total_trips,
        COUNT(DISTINCT rd.stop_id) as total_stops,
        COUNT(*) as total_departures
    FROM {{ ref('stg_gtfs_routes') }} r
    LEFT JOIN {{ ref('route_departures') }} rd ON r.route_id = rd.route_id AND r.agency = rd.agency
    GROUP BY r.route_id, r.agency, r.route_short_name, r.route_long_name
),
streaming_stats AS (
    SELECT
        route_id,
        agency,
        COUNT(*) as streaming_departures,
        AVG(CASE WHEN delay_seconds > 0 THEN delay_seconds ELSE NULL END) as avg_delay_seconds,
        SUM(CASE WHEN delay_seconds BETWEEN -300 AND 300 THEN 1 ELSE 0 END) as on_time_count
    FROM {{ ref('stg_streaming_departures') }}
    WHERE is_real_time = true
    GROUP BY route_id, agency
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

{% if is_incremental() %}
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}

