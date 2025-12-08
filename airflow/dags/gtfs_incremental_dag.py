"""
GTFS Incremental Data Ingestion DAG
Fetches GTFS data incrementally and loads to landing tables
First run: Loads from Aug 1, 2025
Subsequent runs: Only new data
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
import sys
from pathlib import Path
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
    'gtfs_incremental_ingestion',
    default_args=default_args,
    description='GTFS incremental data ingestion to landing tables',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['gtfs', 'incremental', 'landing'],
)

def fetch_gtfs_data(**context):
    """Fetch GTFS data incrementally"""
    script_path = PROJECT_ROOT / "ingestion" / "fetch_gtfs_incremental.py"
    
    import subprocess
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=1800  # 30 minutes
    )
    
    if result.returncode != 0:
        error_msg = result.stderr or result.stdout
        print(f"Error: {error_msg[-1000:]}")
        raise Exception(f"GTFS fetch failed: {error_msg}")
    
    return f"GTFS data fetched: {result.stdout[-500:]}"

def run_dbt_landing_to_raw(**context):
    """Run dbt to transform landing to raw"""
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
            dbt_cmd = [sys.executable, "-c", "import dbt.main; dbt.main.main()", "run", "--select", "landing_to_raw", "--target", "snowflake",
                       "--project-dir", str(dbt_project_dir), "--profiles-dir", str(profiles_dir), "--profile", "transit_dbt"]
        else:
            dbt_cmd = [dbt_path, "run", "--select", "landing_to_raw", "--target", "snowflake",
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
fetch_gtfs = PythonOperator(
    task_id='fetch_gtfs_data',
    python_callable=fetch_gtfs_data,
    dag=dag,
)

dbt_landing_to_raw = PythonOperator(
    task_id='dbt_landing_to_raw',
    python_callable=run_dbt_landing_to_raw,
    dag=dag,
)

# Trigger streaming DAG after GTFS completes
trigger_streaming = TriggerDagRunOperator(
    task_id='trigger_streaming_dag',
    trigger_dag_id='transit_streaming',
    wait_for_completion=False,  # Don't wait, just trigger
    dag=dag,
)

# Set dependencies: Fetch GTFS → Transform → Trigger Streaming
fetch_gtfs >> dbt_landing_to_raw >> trigger_streaming

