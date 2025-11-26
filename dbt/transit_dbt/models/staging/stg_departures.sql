{{
  config(
    materialized='incremental',
    unique_key='departure_key',
    incremental_strategy='merge',
    schema='STAGING',
    tags=['staging', 'streaming']
  )
}}

{#
  Staging model for TransitApp API departures data
  
  Source: RAW.TRANSIT_DEPARTURES (append-only landing table)
  
  This model:
  - Parses the nested JSON structure from TransitApp API
  - Flattens route_departures -> itineraries -> schedule_items
  - Calculates delay metrics
  - Is INCREMENTAL - only processes new data for streaming efficiency
  
  JSON Structure:
  {
    "stop": { "global_stop_id": "...", "stop_name": "..." },
    "departures": {
      "route_departures": [
        {
          "global_route_id": "...",
          "itineraries": [
            {
              "direction_headsign": "...",
              "schedule_items": [
                { "arrival_time": 123456789, "departure_time": 123456789, ... }
              ]
            }
          ]
        }
      ]
    }
  }
#}

WITH source AS (
    SELECT 
        ingestion_id,
        ingestion_timestamp,
        source_file,
        raw_json,
        stop_global_id,
        stop_name,
        fetch_timestamp
    FROM {{ source('raw', 'transit_departures') }}
    {% if is_incremental() %}
    -- Only process new rows since last run (streaming!)
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(ingestion_timestamp), '1900-01-01') FROM {{ this }})
    {% endif %}
),

-- Extract stop info and departures
parsed_base AS (
    SELECT
        ingestion_id,
        ingestion_timestamp,
        source_file,
        fetch_timestamp,
        -- Stop information
        raw_json:stop:global_stop_id::STRING AS stop_global_id,
        raw_json:stop:stop_name::STRING AS stop_name,
        raw_json:stop:stop_lat::FLOAT AS stop_lat,
        raw_json:stop:stop_lon::FLOAT AS stop_lon,
        raw_json:stop:route_type::INT AS route_type,
        raw_json:stop:parent_station:station_name::STRING AS parent_station_name,
        -- Route departures array for flattening
        raw_json:departures:route_departures AS route_departures
    FROM source
    WHERE raw_json IS NOT NULL
),

-- Flatten route_departures array
flattened_routes AS (
    SELECT
        pb.*,
        rd.value:global_route_id::STRING AS route_global_id,
        rd.value:mode::STRING AS mode,
        rd.value:itineraries AS itineraries,
        -- Route display info
        rd.value:route_long_name::STRING AS route_long_name,
        rd.value:route_short_name::STRING AS route_short_name,
        rd.value:route_color::STRING AS route_color
    FROM parsed_base pb,
    LATERAL FLATTEN(input => pb.route_departures, OUTER => TRUE) rd
    WHERE rd.value IS NOT NULL
),

-- Flatten itineraries array
flattened_itineraries AS (
    SELECT
        fr.*,
        it.value:direction_headsign::STRING AS direction_headsign,
        it.value:direction_id::INT AS direction_id,
        it.value:headsign::STRING AS headsign,
        it.value:schedule_items AS schedule_items
    FROM flattened_routes fr,
    LATERAL FLATTEN(input => fr.itineraries, OUTER => TRUE) it
    WHERE it.value IS NOT NULL
),

-- Flatten schedule_items (actual departures)
flattened_departures AS (
    SELECT
        fi.*,
        si.index AS schedule_item_index,
        -- Departure times (Unix timestamps)
        si.value:arrival_time::INT AS arrival_time_unix,
        si.value:departure_time::INT AS departure_time_unix,
        si.value:scheduled_arrival_time::INT AS scheduled_arrival_unix,
        si.value:scheduled_departure_time::INT AS scheduled_departure_unix,
        -- Trip info
        si.value:trip_id::STRING AS trip_id,
        si.value:trip_search_key::STRING AS trip_search_key,
        -- Real-time status
        si.value:is_cancelled::BOOLEAN AS is_cancelled,
        si.value:is_real_time::BOOLEAN AS is_real_time,
        si.value:rt_trip_id::STRING AS rt_trip_id,
        -- Occupancy
        si.value:occupancy_status::STRING AS occupancy_status,
        si.value:bikes_allowed::BOOLEAN AS bikes_allowed
    FROM flattened_itineraries fi,
    LATERAL FLATTEN(input => fi.schedule_items, OUTER => TRUE) si
    WHERE si.value IS NOT NULL
)

SELECT
    -- Generate unique key for incremental merge
    MD5(
        COALESCE(stop_global_id, '') || '|' ||
        COALESCE(route_global_id, '') || '|' ||
        COALESCE(trip_id, '') || '|' ||
        COALESCE(TO_VARCHAR(departure_time_unix), '') || '|' ||
        COALESCE(TO_VARCHAR(ingestion_timestamp), '')
    ) AS departure_key,
    
    -- Ingestion metadata
    ingestion_id,
    ingestion_timestamp,
    source_file,
    fetch_timestamp,
    
    -- Stop information
    stop_global_id,
    stop_name,
    stop_lat,
    stop_lon,
    parent_station_name,
    route_type,
    
    -- Route information
    route_global_id,
    route_long_name,
    route_short_name,
    route_color,
    mode,
    
    -- Direction/Headsign
    direction_headsign,
    direction_id,
    headsign,
    
    -- Departure times (converted from Unix to timestamp)
    TO_TIMESTAMP_NTZ(arrival_time_unix) AS arrival_time,
    TO_TIMESTAMP_NTZ(departure_time_unix) AS departure_time,
    TO_TIMESTAMP_NTZ(scheduled_arrival_unix) AS scheduled_arrival_time,
    TO_TIMESTAMP_NTZ(scheduled_departure_unix) AS scheduled_departure_time,
    
    -- Calculate delay (in seconds)
    CASE 
        WHEN departure_time_unix IS NOT NULL AND scheduled_departure_unix IS NOT NULL 
        THEN departure_time_unix - scheduled_departure_unix
        WHEN arrival_time_unix IS NOT NULL AND scheduled_arrival_unix IS NOT NULL 
        THEN arrival_time_unix - scheduled_arrival_unix
        ELSE NULL
    END AS delay_seconds,
    
    -- Delay status classification
    CASE
        WHEN departure_time_unix IS NULL OR scheduled_departure_unix IS NULL THEN 'UNKNOWN'
        WHEN (departure_time_unix - scheduled_departure_unix) < -60 THEN 'EARLY'
        WHEN (departure_time_unix - scheduled_departure_unix) BETWEEN -60 AND 300 THEN 'ON_TIME'
        WHEN (departure_time_unix - scheduled_departure_unix) BETWEEN 300 AND 600 THEN 'LATE'
        ELSE 'VERY_LATE'
    END AS delay_status,
    
    -- Trip info
    trip_id,
    trip_search_key,
    rt_trip_id,
    
    -- Real-time flags
    is_cancelled,
    is_real_time,
    
    -- Occupancy
    occupancy_status,
    bikes_allowed,
    
    -- Time dimensions for analytics
    DATE(TO_TIMESTAMP_NTZ(departure_time_unix)) AS departure_date,
    HOUR(TO_TIMESTAMP_NTZ(departure_time_unix)) AS departure_hour,
    DAYOFWEEK(TO_TIMESTAMP_NTZ(departure_time_unix)) AS departure_day_of_week,
    DAYNAME(TO_TIMESTAMP_NTZ(departure_time_unix)) AS departure_day_name,
    
    -- Audit
    CURRENT_TIMESTAMP() AS dbt_loaded_at

FROM flattened_departures
WHERE departure_time_unix IS NOT NULL
  AND stop_global_id IS NOT NULL
  AND route_global_id IS NOT NULL
