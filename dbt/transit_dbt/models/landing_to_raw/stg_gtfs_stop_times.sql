-- Staging model: GTFS Stop Times from Landing to Raw
{{ config(
    materialized='incremental',
    unique_key=['trip_id', 'stop_id', 'stop_sequence'],
    incremental_strategy='merge'
) }}

SELECT
    trip_id,
    arrival_time,
    departure_time,
    stop_id,
    CAST(stop_sequence AS INTEGER) as stop_sequence,
    stop_headsign,
    CAST(pickup_type AS INTEGER) as pickup_type,
    CAST(drop_off_type AS INTEGER) as drop_off_type,
    CAST(shape_dist_traveled AS FLOAT) as shape_dist_traveled,
    CAST(timepoint AS INTEGER) as timepoint,
    agency,
    service_date,
    loaded_at
FROM {{ source('landing', 'landing_gtfs_stop_times') }}

{% if is_incremental() %}
    WHERE loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
{% endif %}
