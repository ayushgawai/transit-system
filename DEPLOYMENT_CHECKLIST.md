# Deployment Checklist

## Pre-Deployment

- [ ] AWS account set up with billing alerts configured
- [ ] Snowflake account created (free trial activated, $400 credits)
- [ ] TransitApp API key obtained (request at https://transit.land/api)
- [ ] All environment variables documented and ready
- [ ] Master config file (`config/config.yaml`) configured with actual values
- [ ] Secrets management strategy decided (AWS Secrets Manager, environment variables)

## AWS Infrastructure

- [ ] CloudFormation stack deployed successfully
  - [ ] S3 buckets created (raw, processed, artifacts)
  - [ ] SQS queues created (ingestion, DLQ, Snowpipe notifications)
  - [ ] Lambda execution role created with correct permissions
  - [ ] Snowflake S3 integration role created
  - [ ] EventBridge schedules created
  - [ ] CloudWatch alarms configured
  - [ ] SNS topic for alerts created
- [ ] All CloudFormation outputs saved (bucket names, role ARNs, queue ARNs)

## Snowflake Setup

- [ ] Database `TRANSIT_DB` created
- [ ] Schemas created: `RAW`, `STAGING`, `MARTS`, `ML`
- [ ] Warehouse `TRANSIT_WH` created (X-SMALL, auto-suspend enabled)
- [ ] Roles created: `TRANSIT_ROLE`, `TRANSIT_INGESTION_ROLE`
- [ ] Permissions granted to roles
- [ ] Storage integration created for S3 access
- [ ] External stages created (`TRANSIT_S3_STAGE`, `GTFS_S3_STAGE`)
- [ ] Snowpipe pipes created (`TRANSIT_RAW_PIPE`, `GTFS_ROUTES_PIPE`, `GTFS_STOPS_PIPE`)
- [ ] Notification integration created (SQS) and linked to pipes
- [ ] Snowpipe auto-ingest enabled and tested

## Lambda Functions

- [ ] TransitApp API ingestion Lambda deployed
  - [ ] Code packaged (zip file)
  - [ ] Function created with correct role
  - [ ] Environment variables set (bucket name, queue URL, secrets ARN)
  - [ ] Tested manually
- [ ] GTFS sync Lambda deployed
  - [ ] Code packaged
  - [ ] Function created with correct role
  - [ ] Environment variables set
  - [ ] Tested manually
- [ ] Lambda functions triggered via EventBridge schedules
- [ ] Lambda logs verified in CloudWatch

## Data Ingestion

- [ ] TransitApp API ingestion tested
  - [ ] Data appears in S3 raw bucket
  - [ ] Data loads into Snowflake via Snowpipe
  - [ ] Rate limits respected (5 calls/min)
- [ ] GTFS sync tested
  - [ ] GTFS feeds downloaded successfully
  - [ ] Data appears in S3
  - [ ] Data loads into Snowflake
- [ ] Snowpipe auto-ingestion verified
  - [ ] New files in S3 trigger Snowpipe load
  - [ ] Data appears in `RAW` schema tables
  - [ ] Load history checked for errors

## dbt Project

- [ ] dbt installed (`pip install dbt-snowflake`)
- [ ] `profiles.yml` configured with Snowflake credentials
- [ ] dbt connection tested (`dbt debug`)
- [ ] dbt dependencies installed (`dbt deps`)
- [ ] Staging models run successfully (`dbt run --select staging.*`)
- [ ] Staging models tested (`dbt test --select staging.*`)
- [ ] Marts models run successfully (`dbt run --select marts.*`)
- [ ] Marts models tested (`dbt test --select marts.*`)
- [ ] dbt docs generated (`dbt docs generate`)

## Airflow

- [ ] Airflow environment set up (local Docker or AWS MWAA)
- [ ] Airflow connections configured (AWS, Snowflake)
- [ ] Airflow variables set (function names, bucket names, etc.)
- [ ] DAGs deployed and visible in Airflow UI
- [ ] Ingestion DAG runs successfully
- [ ] Transformation DAG runs successfully
- [ ] ML refresh DAG runs successfully
- [ ] DAG schedules verified
- [ ] DAG failure notifications configured

## ML Models

- [ ] ML model training scripts tested locally
- [ ] Snowpark session configured
- [ ] Training data verified (sufficient historical data)
- [ ] Demand forecast model trained and evaluated
- [ ] Delay forecast model trained and evaluated
- [ ] Crowding forecast model trained and evaluated
- [ ] Forecasts generated and saved to `ML.FORECASTS` table
- [ ] Model metadata saved to `ML.MODEL_METADATA` table
- [ ] ML refresh scheduled in Airflow (daily)

## BI Dashboard

- [ ] BI tool selected and set up (Snowsight/QuickSight/Metabase)
- [ ] Snowflake data source configured
- [ ] Datasets imported (marts tables)
- [ ] Service Reliability dashboard created
- [ ] Demand & Crowding dashboard created
- [ ] Revenue Overlay dashboard created
- [ ] Forecasting dashboard created
- [ ] Decision Support dashboard created
- [ ] Dashboard refresh intervals configured
- [ ] Dashboard access control configured

## Chatbot

- [ ] OpenAI API key obtained (or local LLM configured)
- [ ] Chatbot API server tested locally
- [ ] Chatbot deployed (Lambda or container)
- [ ] API Gateway configured (if using Lambda)
- [ ] Natural language queries tested
- [ ] SQL generation verified
- [ ] Answer formatting verified
- [ ] Error handling tested

## Monitoring & Alerts

- [ ] CloudWatch dashboards created
  - [ ] Lambda invocations, errors, duration
  - [ ] SQS queue depth
  - [ ] S3 bucket sizes
- [ ] CloudWatch alarms configured and tested
  - [ ] Lambda error alarm
  - [ ] SQS queue depth alarm
  - [ ] S3 bucket size alarm
- [ ] SNS topic subscriptions configured (email, Slack, etc.)
- [ ] Snowflake query history monitored
- [ ] Snowflake warehouse credit usage tracked
- [ ] AWS Budgets configured ($10/month threshold)

## Cost Monitoring

- [ ] AWS Free Tier usage tracked
  - [ ] Lambda: 1M requests/month
  - [ ] S3: 5GB storage, 20K GET requests/month
  - [ ] SQS: 1M requests/month
  - [ ] EventBridge: 1M custom events/month
- [ ] Snowflake credits monitored
  - [ ] Daily credit usage < $1 (free tier limits)
  - [ ] Warehouse auto-suspend working
- [ ] Cost alerts configured
- [ ] Monthly budget alert set

## Documentation

- [ ] README.md reviewed and updated
- [ ] Architecture diagram created
- [ ] Setup guide tested end-to-end
- [ ] API documentation created (for chatbot)
- [ ] Dashboard user guide created
- [ ] Troubleshooting guide created

## Testing

- [ ] End-to-end data flow tested
  - [ ] API → S3 → Snowpipe → dbt → marts → dashboard
- [ ] Error scenarios tested
  - [ ] API failure
  - [ ] Snowpipe failure
  - [ ] dbt transformation failure
  - [ ] ML model failure
- [ ] Load testing (if applicable)
- [ ] Security review completed
  - [ ] Secrets not hard-coded
  - [ ] IAM roles follow least privilege
  - [ ] S3 buckets private
  - [ ] Snowflake credentials secure

## Production Readiness

- [ ] Backup strategy defined
  - [ ] S3 versioning enabled
  - [ ] Snowflake data retention policy
- [ ] Disaster recovery plan documented
- [ ] Scaling strategy defined (if needed)
- [ ] Performance baselines established
- [ ] Team training completed
- [ ] Support contact information documented

## Post-Deployment

- [ ] Smoke tests run
- [ ] Initial data quality checks
- [ ] Dashboards verified with real data
- [ ] Chatbot tested with real queries
- [ ] Stakeholder demo completed
- [ ] Feedback collected and prioritized

## Ongoing Maintenance

- [ ] Daily: Check CloudWatch dashboards for errors
- [ ] Weekly: Review Snowflake credit usage
- [ ] Weekly: Review dbt test results
- [ ] Monthly: Retrain ML models
- [ ] Monthly: Review and update documentation
- [ ] Quarterly: Cost optimization review
- [ ] Quarterly: Security audit

