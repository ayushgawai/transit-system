"""
ML Forecast DAG
Generates forecasts using Snowflake ML or local ML based on config
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
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
    'ml_forecast',
    default_args=default_args,
    description='ML forecasting for demand and delays. Auto-triggered by Streaming DAG or runs every 6 hours.',
    schedule_interval='0 */6 * * *',  # Every 6 hours (backup schedule)
    catchup=False,
    tags=['ml', 'forecast', 'analytics'],
)

def run_ml_forecast(**context):
    """Run ML forecast based on warehouse type"""
    from config.warehouse_config import get_warehouse_config
    
    config = get_warehouse_config()
    ml_provider = config.config.get('ml', {}).get('provider', 'local')
    
    if config.is_snowflake() and ml_provider == 'snowflake':
        # Use Snowflake ML
        import subprocess
        dbt_project_dir = PROJECT_ROOT / "dbt" / "transit_dbt"
        profiles_dir = PROJECT_ROOT / "dbt" / "transit_dbt"
        
        # Set Snowflake environment variables
        snowflake_config = config.get_snowflake_config()
        os.environ['SNOWFLAKE_ACCOUNT'] = snowflake_config.get('account', '')
        os.environ['SNOWFLAKE_USER'] = snowflake_config.get('user', '')
        os.environ['SNOWFLAKE_PASSWORD'] = snowflake_config.get('password', '')
        os.environ['SNOWFLAKE_WAREHOUSE'] = snowflake_config.get('warehouse', '')
        os.environ['SNOWFLAKE_DATABASE'] = snowflake_config.get('database', '')
        os.environ['SNOWFLAKE_ROLE'] = snowflake_config.get('role', '')
        os.environ['DBT_PROFILES_DIR'] = str(profiles_dir)
        
        # Run dbt ML models - try multiple methods to find dbt
        import shutil
        
        # Try to find dbt executable
        dbt_path = shutil.which('dbt')
        if not dbt_path:
            # dbt is installed but not in PATH, use direct python import
            dbt_cmd = [sys.executable, "-c", "import dbt.main; dbt.main.main()", "run", "--select", "ml_forecasts", "--target", "snowflake",
                       "--project-dir", str(dbt_project_dir), "--profiles-dir", str(profiles_dir), "--profile", "transit_dbt"]
        else:
            dbt_cmd = [dbt_path, "run", "--select", "ml_forecasts", "--target", "snowflake",
                       "--project-dir", str(dbt_project_dir), "--profiles-dir", str(profiles_dir), "--profile", "transit_dbt"]
        
        env = os.environ.copy()
        env['PATH'] = f"{os.path.expanduser('~/.local/bin')}:{env.get('PATH', '')}"
        env['DBT_PROFILES_DIR'] = str(profiles_dir)
        
        result = subprocess.run(
            dbt_cmd,
            cwd=str(dbt_project_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise Exception(f"Snowflake ML failed: {error_msg}")
        
        return f"Snowflake ML forecast completed: {result.stdout[-500:]}"
    else:
        # Use local ML fallback
        script_path = PROJECT_ROOT / "api" / "ml_forecast_fallback.py"
        
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            raise Exception(f"Local ML failed: {result.stderr}")
        
        return f"Local ML forecast completed: {result.stdout[-500:]}"

ml_forecast = PythonOperator(
    task_id='run_ml_forecast',
    python_callable=run_ml_forecast,
    dag=dag,
)

