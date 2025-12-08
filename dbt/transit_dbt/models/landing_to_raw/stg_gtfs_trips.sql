-- Staging model: GTFS Trips from Landing to Raw
{{ config(
    materialized='incremental',
    unique_key='trip_id',
    incremental_strategy='merge'
) }}

SELECT
    trip_id,
    route_id,
    service_id,
    trip_headsign,
    trip_short_name,
    CAST(direction_id AS INTEGER) as direction_id,
    block_id,
    shape_id,
    CAST(wheelchair_accessible AS INTEGER) as wheelchair_accessible,
    agency,
    loaded_at
FROM {{ source('landing', 'landing_gtfs_trips') }}

{% if is_incremental() %}
    WHERE loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
{% endif %}

