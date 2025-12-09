-- Staging model: GTFS Routes from Landing to Raw
{{ config(
    materialized='incremental',
    unique_key=['route_id', 'agency'],
    incremental_strategy='merge'
) }}

SELECT
    route_id,
    agency_id,
    route_short_name,
    route_long_name,
    route_desc,
    CAST(route_type AS INTEGER) as route_type,
    route_url,
    route_color,
    route_text_color,
    agency,
    loaded_at
FROM {{ source('landing', 'landing_gtfs_routes') }}

{% if is_incremental() %}
    WHERE loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
{% endif %}

