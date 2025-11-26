{{
  config(
    materialized='incremental',
    unique_key='alert_key',
    incremental_strategy='merge',
    schema='STAGING',
    tags=['staging']
  )
}}

{#
  Staging model for TransitApp API alerts data
  
  Source: RAW.TRANSIT_ALERTS (landing table)
  
  Alerts are embedded in departure responses under route_departures.alerts
  This model also processes standalone alert data if available
#}

WITH source_departures AS (
    -- Extract alerts from departure data (they're nested in route_departures)
    SELECT 
        ingestion_id,
        ingestion_timestamp,
        source_file,
        raw_json,
        fetch_timestamp
    FROM {{ source('raw', 'transit_departures') }}
    {% if is_incremental() %}
    WHERE ingestion_timestamp > (SELECT COALESCE(MAX(ingestion_timestamp), '1900-01-01') FROM {{ this }})
    {% endif %}
),

-- Extract alerts from route_departures
flattened_alerts AS (
    SELECT
        s.ingestion_id,
        s.ingestion_timestamp,
        s.source_file,
        s.fetch_timestamp,
        rd.value:global_route_id::STRING AS route_global_id,
        alert.value:title::STRING AS alert_title,
        alert.value:description::STRING AS alert_description,
        alert.value:severity::STRING AS alert_severity,
        alert.value:effect::STRING AS alert_effect,
        alert.value:cause::STRING AS alert_cause,
        alert.value:created_at::INT AS created_at_unix,
        alert.value:updated_at::INT AS updated_at_unix,
        alert.value:active_period AS active_period,
        alert.value:informed_entities AS informed_entities,
        alert.value:url::STRING AS alert_url
    FROM source_departures s,
    LATERAL FLATTEN(input => s.raw_json:departures:route_departures, OUTER => TRUE) rd,
    LATERAL FLATTEN(input => rd.value:alerts, OUTER => TRUE) alert
    WHERE alert.value IS NOT NULL
)

SELECT
    -- Generate unique key
    MD5(
        COALESCE(route_global_id, '') || '|' ||
        COALESCE(alert_title, '') || '|' ||
        COALESCE(TO_VARCHAR(created_at_unix), '') || '|' ||
        COALESCE(TO_VARCHAR(ingestion_timestamp), '')
    ) AS alert_key,
    
    -- Alert info
    alert_title,
    alert_description,
    alert_severity,
    alert_effect,
    alert_cause,
    alert_url,
    
    -- Affected route
    route_global_id,
    
    -- Timestamps
    TO_TIMESTAMP_NTZ(created_at_unix) AS alert_created_at,
    TO_TIMESTAMP_NTZ(updated_at_unix) AS alert_updated_at,
    
    -- Active period (if available)
    active_period,
    
    -- Entities affected
    informed_entities,
    
    -- Metadata
    ingestion_id,
    ingestion_timestamp,
    source_file,
    fetch_timestamp,
    
    -- Audit
    CURRENT_TIMESTAMP() AS dbt_loaded_at

FROM flattened_alerts
WHERE alert_title IS NOT NULL OR alert_description IS NOT NULL
