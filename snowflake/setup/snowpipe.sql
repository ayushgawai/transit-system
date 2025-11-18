-- Snowpipe Setup for Automatic Loading from S3
-- Run this after creating storage integration in Snowflake console

USE DATABASE TRANSIT_DB;
USE SCHEMA RAW;

-- =============================================================================
-- STORAGE INTEGRATION (Run this in Snowflake console or via CLI)
-- =============================================================================

-- Note: Storage integration must be created with AWS IAM role ARN
-- This is typically done via Snowflake console or with AWS role ARN from CloudFormation output
-- Example:
-- CREATE STORAGE INTEGRATION TRANSIT_S3_STORAGE_INTEGRATION
--     TYPE = EXTERNAL_STAGE
--     STORAGE_PROVIDER = 'S3'
--     ENABLED = TRUE
--     STORAGE_AWS_ROLE_ARN = '<role-arn-from-cloudformation>'
--     STORAGE_ALLOWED_LOCATIONS = ('s3://transit-raw-data-<account-id>-<env>/transitapp/', 's3://transit-raw-data-<account-id>-<env>/gtfs/');

-- =============================================================================
-- EXTERNAL STAGE
-- =============================================================================

CREATE STAGE IF NOT EXISTS TRANSIT_S3_STAGE
    STORAGE_INTEGRATION = TRANSIT_S3_STORAGE_INTEGRATION
    URL = 's3://transit-raw-data-<account-id>-<env>/'
    FILE_FORMAT = (TYPE = 'JSON');

-- Separate stage for GTFS files (CSV/text)
CREATE STAGE IF NOT EXISTS GTFS_S3_STAGE
    STORAGE_INTEGRATION = TRANSIT_S3_STORAGE_INTEGRATION
    URL = 's3://transit-raw-data-<account-id>-<env>/gtfs/'
    FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1);

-- =============================================================================
-- SNOWPIPE: Auto-load TransitApp API calls
-- =============================================================================

CREATE PIPE IF NOT EXISTS TRANSIT_RAW_PIPE
    AUTO_INGEST = TRUE
    AS
    COPY INTO TRANSITAPP_API_CALLS
    FROM (
        SELECT 
            $1 AS value,
            METADATA$FILENAME AS metadata$filename,
            METADATA$FILE_ROW_NUMBER AS metadata$file_row_number,
            METADATA$FILE_CONTENT_KEY AS metadata$file_content_key,
            CURRENT_TIMESTAMP() AS load_timestamp
        FROM @TRANSIT_S3_STAGE/transitapp/
    )
    FILE_FORMAT = (TYPE = 'JSON')
    PATTERN = '.*\\.json';

-- =============================================================================
-- SNOWPIPE: Auto-load GTFS Routes
-- =============================================================================

CREATE PIPE IF NOT EXISTS GTFS_ROUTES_PIPE
    AUTO_INGEST = TRUE
    AS
    COPY INTO GTFS_ROUTES
    FROM (
        SELECT 
            $1 AS value,
            METADATA$FILENAME AS metadata$filename,
            CURRENT_TIMESTAMP() AS load_timestamp
        FROM @GTFS_S3_STAGE/.*routes.*\\.txt
    )
    FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1);

-- =============================================================================
-- SNOWPIPE: Auto-load GTFS Stops
-- =============================================================================

CREATE PIPE IF NOT EXISTS GTFS_STOPS_PIPE
    AUTO_INGEST = TRUE
    AS
    COPY INTO GTFS_STOPS
    FROM (
        SELECT 
            $1 AS value,
            METADATA$FILENAME AS metadata$filename,
            CURRENT_TIMESTAMP() AS load_timestamp
        FROM @GTFS_S3_STAGE/.*stops.*\\.txt
    )
    FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1);

-- =============================================================================
-- NOTIFICATION CHANNEL (SQS)
-- =============================================================================

-- Note: Create notification channel with SQS ARN from CloudFormation output
-- This enables auto-ingest for Snowpipe
-- Example:
-- CREATE NOTIFICATION INTEGRATION TRANSIT_SQS_INTEGRATION
--     TYPE = QUEUE
--     NOTIFICATION_PROVIDER = AWS_SQS
--     ENABLED = TRUE
--     DIRECTION = INBOUND
--     AWS_SQS_QUEUE_ARN = '<sqs-queue-arn-from-cloudformation>'
--     AWS_SQS_ROLE_ARN = '<snowflake-s3-role-arn>';

-- After creating notification integration, add to pipes:
-- ALTER PIPE TRANSIT_RAW_PIPE SET NOTIFICATION_INTEGRATION = TRANSIT_SQS_INTEGRATION;
-- ALTER PIPE GTFS_ROUTES_PIPE SET NOTIFICATION_INTEGRATION = TRANSIT_SQS_INTEGRATION;
-- ALTER PIPE GTFS_STOPS_PIPE SET NOTIFICATION_INTEGRATION = TRANSIT_SQS_INTEGRATION;

-- =============================================================================
-- MONITOR SNOWPIPE STATUS
-- =============================================================================

-- Check pipe status
-- SELECT SYSTEM$PIPE_STATUS('TRANSIT_RAW_PIPE');

-- View pipe history
-- SELECT * FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
--     TABLE_NAME => 'RAW.TRANSITAPP_API_CALLS',
--     START_TIME => DATEADD(day, -1, CURRENT_TIMESTAMP())
-- ));

