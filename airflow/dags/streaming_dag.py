"""
Streaming Data DAG
Runs Kafka producer and consumer for streaming Transit API data
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
import sys
from pathlib import Path
import subprocess
import os

# In Airflow container, DAGs are in /opt/airflow/dags
# So PROJECT_ROOT should be /opt/airflow (parent of dags)
# For local testing, use absolute path from environment or calculate relative
if os.path.exists('/opt/airflow'):
    # Running in Airflow container
    PROJECT_ROOT = Path('/opt/airflow')
else:
    # Running locally
    PROJECT_ROOT = Path(__file__).parent.parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

default_args = {
    'owner': 'transit-data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
    'start_date': days_ago(1),
}

dag = DAG(
    'transit_streaming',
    default_args=default_args,
    description='Stream Transit API data via Kafka to landing tables. Auto-triggered by GTFS DAG or runs hourly.',
    schedule_interval='0 * * * *',  # Every hour (backup schedule)
    catchup=False,
    tags=['streaming', 'kafka', 'transit-api'],
)

def run_kafka_producer(**context):
    """Run Kafka producer to fetch and send streaming data"""
    script_path = PROJECT_ROOT / "ingestion" / "kafka_streaming_producer.py"
    
    # Run for 5 minutes then stop (for scheduled runs)
    import signal
    import time
    
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait 5 minutes
    try:
        process.wait(timeout=300)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait()
    
    return "Kafka producer completed"

def run_kafka_consumer(**context):
    """Run Kafka consumer to load streaming data to landing"""
    script_path = PROJECT_ROOT / "ingestion" / "kafka_consumer_to_landing.py"
    
    # Run for 5 minutes
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        process.wait(timeout=300)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait()
    
    return "Kafka consumer completed"

def run_dbt_streaming_to_analytics(**context):
    """Run dbt to transform streaming landing to analytics"""
    import subprocess
    from config.warehouse_config import get_warehouse_config
    
    config = get_warehouse_config()
    dbt_project_dir = PROJECT_ROOT / "dbt" / "transit_dbt"
    profiles_dir = PROJECT_ROOT / "dbt" / "transit_dbt"
    target = 'snowflake'  # Snowflake only
    
    # Set environment variables for Snowflake
    import os
    snowflake_config = config.get_snowflake_config()
    os.environ['SNOWFLAKE_ACCOUNT'] = snowflake_config.get('account', '')
    os.environ['SNOWFLAKE_USER'] = snowflake_config.get('user', '')
    os.environ['SNOWFLAKE_PASSWORD'] = snowflake_config.get('password', '')
    os.environ['SNOWFLAKE_WAREHOUSE'] = snowflake_config.get('warehouse', '')
    os.environ['SNOWFLAKE_DATABASE'] = snowflake_config.get('database', '')
    os.environ['SNOWFLAKE_ROLE'] = snowflake_config.get('role', '')
    os.environ['SNOWFLAKE_SCHEMA'] = snowflake_config.get('schema', 'ANALYTICS')
    
    os.environ['DBT_PROFILES_DIR'] = str(profiles_dir)
    
    # Run dbt - try multiple methods to find dbt
    try:
        import shutil
        
        # Try to find dbt executable
        dbt_path = shutil.which('dbt')
        if not dbt_path:
            # dbt is installed but not in PATH, use direct python import
            dbt_cmd = [sys.executable, "-c", "import dbt.main; dbt.main.main()", "run", "--select", "streaming_to_analytics", "--target", "snowflake",
                       "--project-dir", str(dbt_project_dir), "--profiles-dir", str(profiles_dir), "--profile", "transit_dbt"]
        else:
            dbt_cmd = [dbt_path, "run", "--select", "streaming_to_analytics", "--target", "snowflake",
                       "--project-dir", str(dbt_project_dir), "--profiles-dir", str(profiles_dir), "--profile", "transit_dbt"]
        
        env = os.environ.copy()
        env['PATH'] = f"{os.path.expanduser('~/.local/bin')}:{env.get('PATH', '')}"
        env['DBT_PROFILES_DIR'] = str(profiles_dir)
        
        run_result = subprocess.run(
            dbt_cmd,
            cwd=str(dbt_project_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if run_result.returncode != 0:
            error_msg = run_result.stderr or run_result.stdout
            raise Exception(f"dbt run failed: {error_msg}")
        
        return f"dbt run successful: {run_result.stdout[-500:]}"
    except Exception as e:
        raise Exception(f"dbt error: {str(e)}")

# Define tasks
kafka_producer = PythonOperator(
    task_id='kafka_producer',
    python_callable=run_kafka_producer,
    dag=dag,
)

kafka_consumer = PythonOperator(
    task_id='kafka_consumer',
    python_callable=run_kafka_consumer,
    dag=dag,
)

dbt_streaming = PythonOperator(
    task_id='dbt_streaming_to_analytics',
    python_callable=run_dbt_streaming_to_analytics,
    dag=dag,
)

# Trigger ML Forecast DAG after streaming completes
trigger_ml_forecast = TriggerDagRunOperator(
    task_id='trigger_ml_forecast_dag',
    trigger_dag_id='ml_forecast',
    wait_for_completion=False,  # Don't wait, just trigger
    dag=dag,
)

# Set dependencies: Producer → Consumer → Transform → Trigger ML Forecast
kafka_producer >> kafka_consumer >> dbt_streaming >> trigger_ml_forecast

