{{
  config(
    materialized='view',
    schema='staging',
    tags=['staging']
  )
}}

-- Staging model for GTFS stops data
-- Cleans and normalizes GTFS stops.txt files

WITH raw_stops AS (
    SELECT
        value AS csv_line,
        metadata$filename AS source_file,
        current_timestamp() AS load_timestamp
    FROM {{ var('snowflake_raw_schema') }}.GTFS_STOPS
),

parsed_stops AS (
    SELECT
        SPLIT_PART(csv_line, ',', 1) AS stop_id,
        SPLIT_PART(csv_line, ',', 2) AS stop_code,
        SPLIT_PART(csv_line, ',', 3) AS stop_name,
        SPLIT_PART(csv_line, ',', 4) AS stop_desc,
        SPLIT_PART(csv_line, ',', 5)::DOUBLE AS stop_lat,
        SPLIT_PART(csv_line, ',', 6)::DOUBLE AS stop_lon,
        SPLIT_PART(csv_line, ',', 7) AS zone_id,
        SPLIT_PART(csv_line, ',', 8) AS stop_url,
        SPLIT_PART(csv_line, ',', 9) AS location_type,
        SPLIT_PART(csv_line, ',', 10) AS parent_station,
        source_file,
        load_timestamp
    FROM raw_stops
    WHERE csv_line NOT LIKE 'stop_id%'  -- Skip header row
)

SELECT
    stop_id,
    stop_code,
    stop_name,
    stop_desc,
    stop_lat,
    stop_lon,
    zone_id,
    stop_url,
    location_type::INTEGER AS location_type,
    parent_station,
    source_file,
    load_timestamp,
    current_timestamp() AS created_at
FROM parsed_stops
WHERE stop_id IS NOT NULL
  AND stop_id != ''
  AND stop_lat IS NOT NULL
  AND stop_lon IS NOT NULL

