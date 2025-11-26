{{
  config(
    materialized='incremental',
    unique_key='route_global_id',
    incremental_strategy='merge',
    schema='STAGING',
    tags=['staging']
  )
}}

{#
  Staging model for route dimension
  
  Routes are extracted from departure data (route_departures array)
  This creates a dimension table of unique routes seen in the system
#}

WITH source AS (
    SELECT 
        ingestion_id,
        ingestion_timestamp,
        raw_json,
        fetch_timestamp
    FROM {{ source('raw', 'transit_departures') }}
    {% if is_incremental() %}
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(last_seen_at), '1900-01-01') FROM {{ this }})
    {% endif %}
),

-- Extract route info from departures
flattened_routes AS (
    SELECT
        s.ingestion_timestamp,
        s.fetch_timestamp,
        rd.value:global_route_id::STRING AS route_global_id,
        rd.value:mode::STRING AS mode,
        rd.value:route_long_name::STRING AS route_long_name,
        rd.value:route_short_name::STRING AS route_short_name,
        rd.value:route_color::STRING AS route_color,
        rd.value:route_text_color::STRING AS route_text_color,
        rd.value:fares AS fares,
        rd.value:compact_display_short_name:elements AS display_elements,
        -- Extract agency from global_route_id (format: "AGENCY:route_id")
        SPLIT_PART(rd.value:global_route_id::STRING, ':', 1) AS agency
    FROM source s,
    LATERAL FLATTEN(input => s.raw_json:departures:route_departures, OUTER => TRUE) rd
    WHERE rd.value:global_route_id IS NOT NULL
),

-- Deduplicate and get latest info for each route
ranked_routes AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY route_global_id 
            ORDER BY ingestion_timestamp DESC
        ) AS rn
    FROM flattened_routes
)

SELECT
    route_global_id,
    agency,
    mode,
    route_long_name,
    route_short_name,
    
    -- Display info
    route_color,
    route_text_color,
    
    -- Route type from mode
    CASE UPPER(mode)
        WHEN 'SUBWAY' THEN 1
        WHEN 'METRO' THEN 1
        WHEN 'RAIL' THEN 2
        WHEN 'BUS' THEN 3
        WHEN 'FERRY' THEN 4
        WHEN 'TRAM' THEN 0
        WHEN 'STREETCAR' THEN 0
        ELSE 99
    END AS route_type,
    
    -- Fare info (stored as VARIANT for flexibility)
    fares,
    
    -- Extract min/max fare if available
    fares[0]:price_min:value::FLOAT AS min_fare,
    fares[0]:price_max:value::FLOAT AS max_fare,
    fares[0]:price_min:currency_code::STRING AS fare_currency,
    
    -- Timestamps
    ingestion_timestamp AS first_seen_at,
    ingestion_timestamp AS last_seen_at,
    
    -- Audit
    CURRENT_TIMESTAMP() AS dbt_loaded_at

FROM ranked_routes
WHERE rn = 1
  AND route_global_id IS NOT NULL
