{{
  config(
    materialized='view',
    schema='staging',
    tags=['staging']
  )
}}

-- Staging model for TransitApp API departures data
-- Cleans and normalizes raw JSON from transitapp/departures/ S3 prefix

WITH raw_departures AS (
    SELECT
        PARSE_JSON(value) AS json_data,
        metadata$filename AS source_file,
        metadata$file_row_number AS row_number,
        current_timestamp() AS load_timestamp
    FROM {{ var('snowflake_raw_schema') }}.TRANSITAPP_API_CALLS
    WHERE source_file LIKE '%departures%'
      AND json_data IS NOT NULL
),

flattened_departures AS (
    SELECT
        d.value:departure_id::STRING AS departure_id,
        d.value:stop_id::STRING AS stop_id,
        d.value:route_id::STRING AS route_id,
        d.value:trip_id::STRING AS trip_id,
        d.value:departure_time::TIMESTAMP_NTZ AS departure_time,
        d.value:scheduled_time::TIMESTAMP_NTZ AS scheduled_time,
        d.value:delay_seconds::INTEGER AS delay_seconds,
        d.value:status::STRING AS status,
        d.value:vehicle_id::STRING AS vehicle_id,
        d.value:occupancy_status::STRING AS occupancy_status,
        rd.source_file,
        rd.load_timestamp
    FROM raw_departures rd,
    LATERAL FLATTEN(input => rd.json_data:departures) d
)

SELECT
    departure_id,
    stop_id,
    route_id,
    trip_id,
    departure_time,
    scheduled_time,
    delay_seconds,
    -- Calculate delay status
    CASE
        WHEN delay_seconds < -300 THEN 'EARLY'
        WHEN delay_seconds BETWEEN -300 AND 300 THEN 'ON_TIME'
        WHEN delay_seconds BETWEEN 300 AND 900 THEN 'LATE'
        ELSE 'VERY_LATE'
    END AS delay_status,
    status,
    vehicle_id,
    occupancy_status,
    -- Extract date and time components
    DATE(departure_time) AS departure_date,
    HOUR(departure_time) AS departure_hour,
    DAYOFWEEK(departure_time) AS departure_day_of_week,
    source_file,
    load_timestamp,
    current_timestamp() AS created_at
FROM flattened_departures
WHERE departure_time IS NOT NULL
  AND stop_id IS NOT NULL
  AND route_id IS NOT NULL

