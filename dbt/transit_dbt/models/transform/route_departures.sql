-- Transform model: Route Departures
-- Combines GTFS stop_times with routes and stops
{{ config(
    materialized='table',
    schema='TRANSFORM'
) }}

SELECT
    st.trip_id,
    st.stop_id,
    st.arrival_time,
    st.departure_time,
    st.stop_sequence,
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    r.route_type,
    r.agency,
    s.stop_name,
    s.stop_lat,
    s.stop_lon,
    t.service_id,
    t.trip_headsign,
    st.service_date,
    st.loaded_at
FROM {{ ref('stg_gtfs_stop_times') }} st
LEFT JOIN {{ ref('stg_gtfs_routes') }} r ON st.agency = r.agency
LEFT JOIN {{ ref('stg_gtfs_stops') }} s ON st.stop_id = s.stop_id AND st.agency = s.agency
LEFT JOIN {{ ref('stg_gtfs_trips') }} t ON st.trip_id = t.trip_id AND st.agency = t.agency

