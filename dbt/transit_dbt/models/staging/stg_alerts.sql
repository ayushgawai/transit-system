{{
  config(
    materialized='view',
    schema='staging',
    tags=['staging']
  )
}}

-- Staging model for TransitApp API alerts data
-- Cleans and normalizes raw JSON from transitapp/alerts/ S3 prefix

WITH raw_alerts AS (
    SELECT
        PARSE_JSON(value) AS json_data,
        metadata$filename AS source_file,
        current_timestamp() AS load_timestamp
    FROM {{ var('snowflake_raw_schema') }}.TRANSITAPP_API_CALLS
    WHERE source_file LIKE '%alerts%'
      AND json_data IS NOT NULL
),

flattened_alerts AS (
    SELECT
        a.value:alert_id::STRING AS alert_id,
        a.value:agency_id::STRING AS agency_id,
        a.value:route_id::STRING AS route_id,
        a.value:stop_id::STRING AS stop_id,
        a.value:title::STRING AS title,
        a.value:description::STRING AS description,
        a.value:severity::STRING AS severity,
        a.value:start_time::TIMESTAMP_NTZ AS start_time,
        a.value:end_time::TIMESTAMP_NTZ AS end_time,
        a.value:effect::STRING AS effect,
        rd.source_file,
        rd.load_timestamp
    FROM raw_alerts rd,
    LATERAL FLATTEN(input => rd.json_data:alerts) a
)

SELECT
    alert_id,
    agency_id,
    route_id,
    stop_id,
    title,
    description,
    severity,
    start_time,
    end_time,
    effect,
    -- Calculate alert duration in minutes
    DATEDIFF(MINUTE, start_time, COALESCE(end_time, current_timestamp())) AS duration_minutes,
    -- Check if alert is currently active
    CASE
        WHEN current_timestamp() BETWEEN start_time AND COALESCE(end_time, current_timestamp()) THEN TRUE
        ELSE FALSE
    END AS is_active,
    source_file,
    load_timestamp,
    current_timestamp() AS created_at
FROM flattened_alerts
WHERE alert_id IS NOT NULL

