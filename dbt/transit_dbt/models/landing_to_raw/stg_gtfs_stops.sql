-- Staging model: GTFS Stops from Landing to Raw
{{ config(
    materialized='incremental',
    unique_key='stop_id',
    incremental_strategy='merge'
) }}

SELECT
    stop_id,
    stop_code,
    stop_name,
    stop_desc,
    CAST(stop_lat AS FLOAT) as stop_lat,
    CAST(stop_lon AS FLOAT) as stop_lon,
    zone_id,
    stop_url,
    CAST(location_type AS INTEGER) as location_type,
    parent_station,
    agency,
    loaded_at
FROM {{ source('landing', 'landing_gtfs_stops') }}

{% if is_incremental() %}
    WHERE loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
{% endif %}

