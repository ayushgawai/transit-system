-- Staging model: Streaming Departures from Landing to Analytics
{{ config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge'
) }}

SELECT
    id,
    timestamp,
    global_stop_id as stop_id,
    stop_name,
    global_route_id as route_id,
    route_short_name,
    route_long_name,
    agency,
    city,
    scheduled_departure_time,
    departure_time as actual_departure_time,
    is_real_time,
    trip_search_key,
    delay_seconds,
    consumed_at as load_timestamp
FROM {{ source('landing', 'landing_streaming_departures') }}

{% if is_incremental() %}
    WHERE consumed_at > (SELECT MAX(load_timestamp) FROM {{ this }})
{% endif %}

