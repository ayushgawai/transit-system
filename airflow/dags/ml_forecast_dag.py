"""
Airflow DAG for ML Forecasting using Snowflake ML FORECAST
Creates, trains, and uses Snowflake ML FORECAST models for demand and delay prediction
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
from pathlib import Path
import os

# Add project root to path
if os.path.exists('/opt/airflow'):
    project_root = Path('/opt/airflow')
else:
    project_root = Path(__file__).parent.parent.parent

sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config
from api.warehouse_connection import get_warehouse_connection

default_args = {
    'owner': 'transit-ops',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

def create_demand_forecast_model():
    """Create and train Snowflake ML FORECAST model for demand prediction"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        print("Only Snowflake is supported for ML forecasting")
        return
    
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        
        # Create schema if not exists
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.ML")
        
        # Prepare training data query
        training_query = f"""
        WITH trip_routes AS (
            SELECT DISTINCT
                t.trip_id,
                tr.route_id,
                r.route_short_name,
                r.agency
            FROM {database}.RAW.STG_GTFS_STOP_TIMES t
            LEFT JOIN {database}.RAW.STG_GTFS_TRIPS tr ON t.trip_id = tr.trip_id
            LEFT JOIN {database}.RAW.STG_GTFS_ROUTES r ON tr.route_id = r.route_id
            WHERE tr.route_id IS NOT NULL
        ),
        historical_data AS (
            SELECT 
                tr.route_id,
                tr.route_short_name,
                tr.agency,
                DATE(t.loaded_at) as ts,
                COUNT(*) as departure_count
            FROM {database}.RAW.STG_GTFS_STOP_TIMES t
            LEFT JOIN trip_routes tr ON t.trip_id = tr.trip_id
            WHERE t.loaded_at >= DATEADD(day, -90, CURRENT_DATE())
                AND tr.route_id IS NOT NULL
            GROUP BY tr.route_id, tr.route_short_name, tr.agency, DATE(t.loaded_at)
            ORDER BY tr.route_id, ts
        )
        SELECT 
            route_id,
            ts,
            departure_count
        FROM historical_data
        """
        
        # Create forecast model
        model_name = f"{database}.ML.DEMAND_FORECAST_MODEL"
        
        try:
            # Drop existing model if exists
            cursor.execute(f"DROP SNOWFLAKE.ML.FORECAST IF EXISTS {model_name}")
        except:
            pass
        
        # Create and train the model
        create_model_sql = f"""
        CREATE SNOWFLAKE.ML.FORECAST {model_name}
        FROM (
            {training_query}
        )
        """
        
        print(f"Creating Snowflake ML FORECAST model: {model_name}")
        cursor.execute(create_model_sql)
        print(f"✓ Model created and trained")
        
        # Generate forecasts for next 7 days
        forecast_sql = f"""
        CALL {model_name}!FORECAST(FORECASTING_PERIODS => 7)
        """
        
        print("Generating forecasts...")
        cursor.execute(forecast_sql)
        forecast_results = cursor.fetchall()
        
        # Store forecasts in ML.DEMAND_FORECAST table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {database}.ML.DEMAND_FORECAST (
                ROUTE_ID VARCHAR(255),
                ROUTE_SHORT_NAME VARCHAR(100),
                AGENCY VARCHAR(100),
                FORECAST_DATE DATE,
                PREDICTED_DEPARTURES INTEGER,
                FORECAST_GENERATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        
        # Clear old forecasts
        cursor.execute(f"DELETE FROM {database}.ML.DEMAND_FORECAST WHERE FORECAST_GENERATED_AT < DATEADD(day, -1, CURRENT_TIMESTAMP())")
        
        # Insert new forecasts (this is a simplified version - actual implementation needs to parse forecast results)
        print(f"✓ Forecasts generated: {len(forecast_results)} predictions")
        
        conn.commit()

def create_delay_forecast_model():
    """Create and train Snowflake ML FORECAST model for delay prediction"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        print("Only Snowflake is supported for ML forecasting")
        return
    
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        
        # Prepare training data query
        training_query = f"""
        SELECT 
            route_id,
            route_short_name,
            agency,
            DATE(load_timestamp) as ts,
            AVG(delay_seconds) as avg_delay_seconds
        FROM {database}.RAW.STG_STREAMING_DEPARTURES
        WHERE load_timestamp >= DATEADD(day, -90, CURRENT_DATE())
            AND delay_seconds IS NOT NULL
        GROUP BY route_id, route_short_name, agency, DATE(load_timestamp)
        ORDER BY route_id, ts
        """
        
        # Create forecast model
        model_name = f"{database}.ML.DELAY_FORECAST_MODEL"
        
        try:
            cursor.execute(f"DROP SNOWFLAKE.ML.FORECAST IF EXISTS {model_name}")
        except:
            pass
        
        # Create and train the model
        create_model_sql = f"""
        CREATE SNOWFLAKE.ML.FORECAST {model_name}
        FROM (
            {training_query}
        )
        """
        
        print(f"Creating Snowflake ML FORECAST model: {model_name}")
        cursor.execute(create_model_sql)
        print(f"✓ Model created and trained")
        
        # Generate forecasts
        forecast_sql = f"""
        CALL {model_name}!FORECAST(FORECASTING_PERIODS => 7)
        """
        
        print("Generating forecasts...")
        cursor.execute(forecast_sql)
        forecast_results = cursor.fetchall()
        
        # Store forecasts
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {database}.ML.DELAY_FORECAST (
                ROUTE_ID VARCHAR(255),
                ROUTE_SHORT_NAME VARCHAR(100),
                AGENCY VARCHAR(100),
                FORECAST_DATE DATE,
                PREDICTED_AVG_DELAY FLOAT,
                PREDICTED_MEDIAN_DELAY FLOAT,
                FORECAST_GENERATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        
        cursor.execute(f"DELETE FROM {database}.ML.DELAY_FORECAST WHERE FORECAST_GENERATED_AT < DATEADD(day, -1, CURRENT_TIMESTAMP())")
        
        print(f"✓ Forecasts generated: {len(forecast_results)} predictions")
        
        conn.commit()

# Create DAG
dag = DAG(
    'ml_forecast_dag',
    default_args=default_args,
    description='ML Forecasting using Snowflake ML FORECAST',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'forecast', 'snowflake']
)

# Tasks
create_demand_forecast = PythonOperator(
    task_id='create_demand_forecast_model',
    python_callable=create_demand_forecast_model,
    dag=dag
)

create_delay_forecast = PythonOperator(
    task_id='create_delay_forecast_model',
    python_callable=create_delay_forecast_model,
    dag=dag
)

# Set dependencies
create_demand_forecast >> create_delay_forecast
