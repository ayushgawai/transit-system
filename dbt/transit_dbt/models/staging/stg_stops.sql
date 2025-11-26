{{
  config(
    materialized='incremental',
    unique_key='stop_key',
    incremental_strategy='merge',
    schema='STAGING',
    tags=['staging']
  )
}}

{#
  Staging model for TransitApp API stops data
  
  Source: RAW.TRANSIT_STOPS (landing table)
  
  This model:
  - Parses the stops array from TransitApp nearby_stops API
  - Extracts stop details including parent stations
  - Is INCREMENTAL to handle updates efficiently
  
  JSON Structure:
  {
    "stops": [
      {
        "global_stop_id": "BART:3311",
        "stop_name": "Civic Center / UN Plaza",
        "stop_lat": 37.779,
        "stop_lon": -122.413,
        "route_type": 1,
        "parent_station": {
          "global_stop_id": "BART:2506",
          "station_name": "Civic Center BART"
        },
        ...
      }
    ]
  }
#}

WITH source AS (
    SELECT 
        ingestion_id,
        ingestion_timestamp,
        source_file,
        raw_json,
        location_lat,
        location_lon,
        fetch_timestamp
    FROM {{ source('raw', 'transit_stops') }}
    {% if is_incremental() %}
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(ingestion_timestamp), '1900-01-01') FROM {{ this }})
    {% endif %}
),

-- Flatten stops array
flattened_stops AS (
    SELECT
        s.ingestion_id,
        s.ingestion_timestamp,
        s.source_file,
        s.location_lat AS query_lat,
        s.location_lon AS query_lon,
        s.fetch_timestamp,
        -- Stop details
        stop.value:global_stop_id::STRING AS stop_global_id,
        stop.value:stop_name::STRING AS stop_name,
        stop.value:stop_code::STRING AS stop_code,
        stop.value:stop_lat::FLOAT AS stop_lat,
        stop.value:stop_lon::FLOAT AS stop_lon,
        stop.value:route_type::INT AS route_type,
        stop.value:location_type::INT AS location_type,
        stop.value:distance::INT AS distance_meters,
        stop.value:wheelchair_boarding::INT AS wheelchair_boarding,
        -- Parent station info
        stop.value:parent_station:global_stop_id::STRING AS parent_station_id,
        stop.value:parent_station:station_name::STRING AS parent_station_name,
        stop.value:parent_station_global_stop_id::STRING AS parent_station_global_id,
        -- Raw/RT IDs
        stop.value:raw_stop_id::STRING AS raw_stop_id,
        stop.value:rt_stop_id::STRING AS rt_stop_id,
        -- City info
        stop.value:city_name::STRING AS city_name
    FROM source s,
    LATERAL FLATTEN(input => s.raw_json:stops, OUTER => TRUE) stop
    WHERE stop.value IS NOT NULL
)

SELECT
    -- Generate unique key for incremental merge
    MD5(COALESCE(stop_global_id, '') || '|' || COALESCE(TO_VARCHAR(ingestion_timestamp), '')) AS stop_key,
    
    -- Use stop_global_id as the business key
    stop_global_id,
    stop_name,
    stop_code,
    stop_lat,
    stop_lon,
    
    -- Route type (0=Tram, 1=Subway, 2=Rail, 3=Bus, etc.)
    route_type,
    CASE route_type
        WHEN 0 THEN 'Tram/Streetcar'
        WHEN 1 THEN 'Subway/Metro'
        WHEN 2 THEN 'Rail'
        WHEN 3 THEN 'Bus'
        WHEN 4 THEN 'Ferry'
        WHEN 5 THEN 'Cable Tram'
        WHEN 6 THEN 'Aerial Lift'
        WHEN 7 THEN 'Funicular'
        WHEN 11 THEN 'Trolleybus'
        WHEN 12 THEN 'Monorail'
        ELSE 'Other'
    END AS route_type_name,
    
    -- Location type
    location_type,
    CASE location_type
        WHEN 0 THEN 'Stop/Platform'
        WHEN 1 THEN 'Station'
        WHEN 2 THEN 'Entrance/Exit'
        WHEN 3 THEN 'Generic Node'
        WHEN 4 THEN 'Boarding Area'
        ELSE 'Unknown'
    END AS location_type_name,
    
    -- Parent station
    COALESCE(parent_station_id, parent_station_global_id) AS parent_station_id,
    parent_station_name,
    
    -- Accessibility
    wheelchair_boarding,
    CASE wheelchair_boarding
        WHEN 0 THEN 'No Information'
        WHEN 1 THEN 'Accessible'
        WHEN 2 THEN 'Not Accessible'
        ELSE 'Unknown'
    END AS wheelchair_status,
    
    -- Distance from query point
    distance_meters,
    
    -- IDs
    raw_stop_id,
    rt_stop_id,
    
    -- Location
    city_name,
    query_lat,
    query_lon,
    
    -- Metadata
    ingestion_id,
    ingestion_timestamp,
    source_file,
    fetch_timestamp,
    
    -- Audit
    CURRENT_TIMESTAMP() AS dbt_loaded_at

FROM flattened_stops
WHERE stop_global_id IS NOT NULL
