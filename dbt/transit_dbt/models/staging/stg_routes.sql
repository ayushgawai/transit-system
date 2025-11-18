{{
  config(
    materialized='view',
    schema='staging',
    tags=['staging']
  )
}}

-- Staging model for GTFS routes data
-- Cleans and normalizes GTFS routes.txt files

WITH raw_routes AS (
    SELECT
        value AS csv_line,
        metadata$filename AS source_file,
        current_timestamp() AS load_timestamp
    FROM {{ var('snowflake_raw_schema') }}.GTFS_ROUTES
),

parsed_routes AS (
    SELECT
        SPLIT_PART(csv_line, ',', 1) AS route_id,
        SPLIT_PART(csv_line, ',', 2) AS agency_id,
        SPLIT_PART(csv_line, ',', 3) AS route_short_name,
        SPLIT_PART(csv_line, ',', 4) AS route_long_name,
        SPLIT_PART(csv_line, ',', 5) AS route_desc,
        SPLIT_PART(csv_line, ',', 6) AS route_type,
        SPLIT_PART(csv_line, ',', 7) AS route_url,
        SPLIT_PART(csv_line, ',', 8) AS route_color,
        SPLIT_PART(csv_line, ',', 9) AS route_text_color,
        source_file,
        load_timestamp
    FROM raw_routes
    WHERE csv_line NOT LIKE 'route_id%'  -- Skip header row
)

SELECT
    route_id,
    agency_id,
    route_short_name,
    route_long_name,
    route_desc,
    route_type::INTEGER AS route_type,
    -- Map route_type to human-readable name
    CASE route_type::INTEGER
        WHEN 0 THEN 'Tram, Streetcar, Light rail'
        WHEN 1 THEN 'Subway, Metro'
        WHEN 2 THEN 'Rail'
        WHEN 3 THEN 'Bus'
        WHEN 4 THEN 'Ferry'
        WHEN 5 THEN 'Cable tram'
        WHEN 6 THEN 'Aerial lift'
        WHEN 7 THEN 'Funicular'
        ELSE 'Unknown'
    END AS route_type_name,
    route_url,
    route_color,
    route_text_color,
    source_file,
    load_timestamp,
    current_timestamp() AS created_at
FROM parsed_routes
WHERE route_id IS NOT NULL
  AND route_id != ''

