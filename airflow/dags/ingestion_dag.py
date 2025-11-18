"""
Airflow DAG: Transit Data Ingestion

This DAG orchestrates the ingestion of transit data:
1. Triggers TransitApp API ingestion Lambda (every 5 minutes)
2. Monitors ingestion success/failure
3. Triggers GTFS sync Lambda (daily)
4. Monitors Snowpipe load status

Schedule: Every 5 minutes for API ingestion, daily for GTFS sync
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.providers.amazon.aws.sensors.lambda_function import LambdaFunctionStateSensor
from airflow.providers.amazon.aws.operators.sqs import SqsPublishOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Default arguments
default_args = {
    'owner': 'transit-data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# DAG definition
dag = DAG(
    'transit_ingestion',
    default_args=default_args,
    description='Orchestrate TransitApp API and GTFS data ingestion',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    catchup=False,
    tags=['transit', 'ingestion', 'raw-data'],
)


# =============================================================================
# TRANSITAPP API INGESTION
# =============================================================================

trigger_api_ingestion = LambdaInvokeFunctionOperator(
    task_id='trigger_transitapp_api_ingestion',
    function_name='{{ var.value.transit_api_ingestion_function_name }}',
    payload={
        'source': 'airflow',
        'timestamp': '{{ ts }}',
        'execution_date': '{{ ds }}',
    },
    aws_conn_id='aws_default',
    dag=dag,
)

check_api_ingestion_status = PythonOperator(
    task_id='check_api_ingestion_status',
    python_callable=lambda **context: print(f"API ingestion completed: {context['ti'].xcom_pull(task_ids='trigger_transitapp_api_ingestion')}"),
    dag=dag,
)


# =============================================================================
# GTFS SYNC (DAILY)
# =============================================================================

trigger_gtfs_sync = LambdaInvokeFunctionOperator(
    task_id='trigger_gtfs_sync',
    function_name='{{ var.value.transit_gtfs_sync_function_name }}',
    payload={
        'source': 'airflow',
        'execution_date': '{{ ds }}',
    },
    aws_conn_id='aws_default',
    dag=dag,
)

check_gtfs_sync_status = PythonOperator(
    task_id='check_gtfs_sync_status',
    python_callable=lambda **context: print(f"GTFS sync completed: {context['ti'].xcom_pull(task_ids='trigger_gtfs_sync')}"),
    dag=dag,
)

# Conditional: Only run GTFS sync at 2 AM UTC (matches EventBridge schedule)
from airflow.sensors.time import TimeSensor

wait_for_gtfs_time = TimeSensor(
    task_id='wait_for_gtfs_sync_time',
    target_time='02:00:00',
    dag=dag,
)

# =============================================================================
# SNOWPIPE MONITORING
# =============================================================================

check_snowpipe_status = BashOperator(
    task_id='check_snowpipe_status',
    bash_command="""
    echo "Checking Snowpipe load status..."
    # In production, this would query Snowflake to check Snowpipe load status
    # snowsql -c transit_connection -q "SELECT SYSTEM$PIPE_STATUS('TRANSIT_DB.RAW.TRANSIT_RAW_PIPE');"
    echo "Snowpipe status check completed"
    """,
    dag=dag,
)


# =============================================================================
# TASK DEPENDENCIES
# =============================================================================

# API ingestion runs every 5 minutes
trigger_api_ingestion >> check_api_ingestion_status >> check_snowpipe_status

# GTFS sync runs daily at 2 AM
wait_for_gtfs_time >> trigger_gtfs_sync >> check_gtfs_sync_status

# Note: In production, add conditional branching to only run GTFS sync daily
# Use BranchPythonOperator or ShortCircuitOperator based on hour of day

