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
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.ANALYTICS_ML")
        
        print("Preparing training data view for demand forecast...")
        
        # Create a view with time series data for ML FORECAST
        # We need: SERIES (route_id), TIMESTAMP (date), TARGET (departure_count)
        # Use route performance data to create historical time series
        view_sql = f"""
        CREATE OR REPLACE VIEW {database}.ANALYTICS_ML.VW_DEMAND_TRAINING_DATA AS
        WITH date_series AS (
            SELECT DATEADD(day, -ROW_NUMBER() OVER (ORDER BY 1), CURRENT_DATE()) as DATE
            FROM TABLE(GENERATOR(ROWCOUNT => 90))
        ),
        route_daily AS (
            SELECT 
                rp.route_id,
                ds.DATE,
                rp.total_departures as DEPARTURE_COUNT
            FROM {database}.ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE rp
            CROSS JOIN date_series ds
            WHERE rp.route_id IS NOT NULL
                AND rp.total_departures > 0
        )
        SELECT 
            route_id as SERIES,
            DATE,
            DEPARTURE_COUNT
        FROM route_daily
        ORDER BY route_id, DATE
        """
        
        try:
            cursor.execute(view_sql)
            print("✓ Created training data view")
        except Exception as e:
            print(f"⚠️  Error creating view: {e}")
            # Fallback: use route performance data
            view_sql = f"""
            CREATE OR REPLACE VIEW {database}.ANALYTICS_ML.VW_DEMAND_TRAINING_DATA AS
            SELECT 
                route_id as SERIES,
                CURRENT_DATE() as DATE,
                total_departures as DEPARTURE_COUNT
            FROM {database}.ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE
            WHERE route_id IS NOT NULL
            """
            cursor.execute(view_sql)
            print("✓ Created fallback training data view")
        
        # Check if we have data
        cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS_ML.VW_DEMAND_TRAINING_DATA")
        data_count = cursor.fetchone()[0]
        print(f"Training data records: {data_count}")
        
        if data_count < 10:
            print("⚠️  Insufficient training data. Skipping ML model creation.")
            return
        
        # Create the ML FORECAST model using proper syntax
        model_name = f"{database}.ANALYTICS_ML.DEMAND_FORECAST_MODEL"
        
        try:
            cursor.execute(f"DROP SNOWFLAKE.ML.FORECAST IF EXISTS {model_name}")
            print(f"✓ Dropped existing model if exists")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create ML FORECAST model with proper syntax
        # Build SQL carefully to preserve $REFERENCE - use format() instead of f-string for the $ part
        view_ref = f"{database}.ANALYTICS_ML.VW_DEMAND_TRAINING_DATA"
        # Build SQL with explicit $REFERENCE to avoid f-string issues
        create_model_sql = """CREATE OR REPLACE SNOWFLAKE.ML.FORECAST {model_name}(
            INPUT_DATA => SYSTEM$REFERENCE('VIEW', '{view_ref}'),
            SERIES_COLNAME => 'SERIES',
            TIMESTAMP_COLNAME => 'DATE',
            TARGET_COLNAME => 'DEPARTURE_COUNT',
            CONFIG_OBJECT => {{ 'ON_ERROR': 'SKIP' }}
        )""".format(model_name=model_name, view_ref=view_ref)
        
        print(f"Creating Snowflake ML FORECAST model: {model_name}")
        try:
            cursor.execute(create_model_sql)
            print(f"✓ Model created and trained successfully")
        except Exception as e:
            print(f"✗ Error creating model: {e}")
            raise
        
        # Generate forecasts for next 7 days
        print("Generating forecasts...")
        forecast_sql = f"""
        BEGIN
            CALL {model_name}!FORECAST(
                FORECASTING_PERIODS => 7,
                CONFIG_OBJECT => {{'prediction_interval': 0.95}}
            );
            LET x := SQLID;
            CREATE OR REPLACE TABLE {database}.ANALYTICS_ML.DEMAND_FORECAST_TEMP AS 
            SELECT * FROM TABLE(RESULT_SCAN(:x));
        END;
        """
        
        try:
            cursor.execute(forecast_sql)
            print("✓ Forecasts generated")
        except Exception as e:
            print(f"✗ Error generating forecasts: {e}")
            raise
        
        # Create final forecast table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {database}.ANALYTICS_ML.DEMAND_FORECAST (
                ROUTE_ID VARCHAR(255),
                ROUTE_SHORT_NAME VARCHAR(100),
                AGENCY VARCHAR(100),
                FORECAST_DATE DATE,
                PREDICTED_DEPARTURES INTEGER,
                LOWER_BOUND INTEGER,
                UPPER_BOUND INTEGER,
                FORECAST_GENERATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        
        # Clear old forecasts
        cursor.execute(f"DELETE FROM {database}.ANALYTICS_ML.DEMAND_FORECAST WHERE FORECAST_GENERATED_AT < DATEADD(day, -1, CURRENT_TIMESTAMP())")
        
        # Insert forecasts from temp table
        insert_sql = f"""
        INSERT INTO {database}.ANALYTICS_ML.DEMAND_FORECAST 
        (ROUTE_ID, ROUTE_SHORT_NAME, AGENCY, FORECAST_DATE, PREDICTED_DEPARTURES, LOWER_BOUND, UPPER_BOUND, FORECAST_GENERATED_AT)
        SELECT 
            REPLACE(SERIES, '"', '') as ROUTE_ID,
            REPLACE(SERIES, '"', '') as ROUTE_SHORT_NAME,
            'UNKNOWN' as AGENCY,
            TS as FORECAST_DATE,
            CAST(FORECAST AS INTEGER) as PREDICTED_DEPARTURES,
            CAST(LOWER_BOUND AS INTEGER) as LOWER_BOUND,
            CAST(UPPER_BOUND AS INTEGER) as UPPER_BOUND,
            CURRENT_TIMESTAMP() as FORECAST_GENERATED_AT
        FROM {database}.ANALYTICS_ML.DEMAND_FORECAST_TEMP
        WHERE TS >= CURRENT_DATE()
        """
        
        try:
            cursor.execute(insert_sql)
            inserted_count = cursor.rowcount
            print(f"✓ Inserted {inserted_count} forecast records")
        except Exception as e:
            print(f"✗ Error inserting forecasts: {e}")
            # Try to get route metadata and join
            insert_sql = f"""
            INSERT INTO {database}.ANALYTICS_ML.DEMAND_FORECAST 
            (ROUTE_ID, ROUTE_SHORT_NAME, AGENCY, FORECAST_DATE, PREDICTED_DEPARTURES, LOWER_BOUND, UPPER_BOUND, FORECAST_GENERATED_AT)
            SELECT 
                REPLACE(f.SERIES, '"', '') as ROUTE_ID,
                COALESCE(r.route_short_name, REPLACE(f.SERIES, '"', '')) as ROUTE_SHORT_NAME,
                COALESCE(r.agency, 'UNKNOWN') as AGENCY,
                f.TS as FORECAST_DATE,
                CAST(f.FORECAST AS INTEGER) as PREDICTED_DEPARTURES,
                CAST(f.LOWER_BOUND AS INTEGER) as LOWER_BOUND,
                CAST(f.UPPER_BOUND AS INTEGER) as UPPER_BOUND,
                CURRENT_TIMESTAMP() as FORECAST_GENERATED_AT
            FROM {database}.ANALYTICS_ML.DEMAND_FORECAST_TEMP f
            LEFT JOIN {database}.ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE r 
                ON REPLACE(f.SERIES, '"', '') = r.route_id
            WHERE f.TS >= CURRENT_DATE()
            """
            cursor.execute(insert_sql)
            inserted_count = cursor.rowcount
            print(f"✓ Inserted {inserted_count} forecast records (with route metadata)")
        
        # Clean up temp table
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {database}.ANALYTICS_ML.DEMAND_FORECAST_TEMP")
        except:
            pass
        
        # Verify data
        cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS_ML.DEMAND_FORECAST WHERE FORECAST_GENERATED_AT >= DATEADD(hour, -1, CURRENT_TIMESTAMP())")
        final_count = cursor.fetchone()[0]
        print(f"✓ Final forecast records: {final_count}")
        
        conn.commit()
        print("✓ Demand forecast model completed successfully")

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
        
        # Check if we have streaming data
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM {database}.ANALYTICS_RAW.STG_STREAMING_DEPARTURES
            WHERE delay_seconds IS NOT NULL
                AND load_timestamp >= DATEADD(day, -90, CURRENT_DATE())
        """)
        delay_data_count = cursor.fetchone()[0]
        
        if delay_data_count < 50:
            print(f"⚠️  Insufficient delay data ({delay_data_count} records). Skipping delay forecast.")
            return
        
        print("Preparing training data view for delay forecast...")
        
        # Create view for delay training data
        view_sql = f"""
        CREATE OR REPLACE VIEW {database}.ANALYTICS_ML.VW_DELAY_TRAINING_DATA AS
        SELECT 
            route_id as SERIES,
            DATE(load_timestamp) as DATE,
            AVG(delay_seconds) as AVG_DELAY_SECONDS
        FROM {database}.ANALYTICS_RAW.STG_STREAMING_DEPARTURES
        WHERE load_timestamp >= DATEADD(day, -90, CURRENT_DATE())
            AND delay_seconds IS NOT NULL
            AND route_id IS NOT NULL
        GROUP BY route_id, DATE(load_timestamp)
        HAVING COUNT(*) >= 5  -- At least 5 records per day
        ORDER BY route_id, DATE
        """
        
        try:
            cursor.execute(view_sql)
            print("✓ Created delay training data view")
        except Exception as e:
            print(f"✗ Error creating delay view: {e}")
            return
        
        # Check data count
        cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS_ML.VW_DELAY_TRAINING_DATA")
        data_count = cursor.fetchone()[0]
        print(f"Delay training data records: {data_count}")
        
        if data_count < 10:
            print("⚠️  Insufficient delay training data. Skipping.")
            return
        
        # Create ML FORECAST model
        model_name = f"{database}.ANALYTICS_ML.DELAY_FORECAST_MODEL"
        
        try:
            cursor.execute(f"DROP SNOWFLAKE.ML.FORECAST IF EXISTS {model_name}")
        except:
            pass
        
        view_ref = f"{database}.ANALYTICS_ML.VW_DELAY_TRAINING_DATA"
        sql_parts = [
            f'CREATE OR REPLACE SNOWFLAKE.ML.FORECAST {model_name}(',
            '    INPUT_DATA => SYSTEM',
            '$',
            'REFERENCE(\'VIEW\', \'',
            view_ref,
            '\'),',
            '    SERIES_COLNAME => \'SERIES\',',
            '    TIMESTAMP_COLNAME => \'DATE\',',
            '    TARGET_COLNAME => \'AVG_DELAY_SECONDS\',',
            '    CONFIG_OBJECT => { \'ON_ERROR\': \'SKIP\' }',
            ')'
        ]
        create_model_sql = ''.join(sql_parts)
        if 'SYSTEM$REFERENCE' not in create_model_sql:
            raise ValueError(f"SYSTEM$REFERENCE lost! SQL: {create_model_sql[:200]}")
        
        print(f"Creating Snowflake ML FORECAST model: {model_name}")
        try:
            cursor.execute(create_model_sql)
            print(f"✓ Delay model created and trained")
        except Exception as e:
            print(f"✗ Error creating delay model: {e}")
            return
        
        # Generate forecasts
        forecast_sql = f"""
        BEGIN
            CALL {model_name}!FORECAST(
                FORECASTING_PERIODS => 7,
                CONFIG_OBJECT => {{'prediction_interval': 0.95}}
            );
            LET x := SQLID;
            CREATE OR REPLACE TABLE {database}.ANALYTICS_ML.DELAY_FORECAST_TEMP AS 
            SELECT * FROM TABLE(RESULT_SCAN(:x));
        END;
        """
        
        try:
            cursor.execute(forecast_sql)
            print("✓ Delay forecasts generated")
        except Exception as e:
            print(f"✗ Error generating delay forecasts: {e}")
            return
        
        # Create final table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {database}.ANALYTICS_ML.DELAY_FORECAST (
                ROUTE_ID VARCHAR(255),
                ROUTE_SHORT_NAME VARCHAR(100),
                AGENCY VARCHAR(100),
                FORECAST_DATE DATE,
                PREDICTED_AVG_DELAY FLOAT,
                PREDICTED_MEDIAN_DELAY FLOAT,
                LOWER_BOUND FLOAT,
                UPPER_BOUND FLOAT,
                FORECAST_GENERATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        
        cursor.execute(f"DELETE FROM {database}.ANALYTICS_ML.DELAY_FORECAST WHERE FORECAST_GENERATED_AT < DATEADD(day, -1, CURRENT_TIMESTAMP())")
        
        # Insert forecasts
        insert_sql = f"""
        INSERT INTO {database}.ANALYTICS_ML.DELAY_FORECAST 
        (ROUTE_ID, ROUTE_SHORT_NAME, AGENCY, FORECAST_DATE, PREDICTED_AVG_DELAY, PREDICTED_MEDIAN_DELAY, LOWER_BOUND, UPPER_BOUND, FORECAST_GENERATED_AT)
        SELECT 
            REPLACE(f.SERIES, '"', '') as ROUTE_ID,
            COALESCE(r.route_short_name, REPLACE(f.SERIES, '"', '')) as ROUTE_SHORT_NAME,
            COALESCE(r.agency, 'UNKNOWN') as AGENCY,
            f.TS as FORECAST_DATE,
            CAST(f.FORECAST AS FLOAT) as PREDICTED_AVG_DELAY,
            CAST(f.FORECAST AS FLOAT) as PREDICTED_MEDIAN_DELAY,
            CAST(f.LOWER_BOUND AS FLOAT) as LOWER_BOUND,
            CAST(f.UPPER_BOUND AS FLOAT) as UPPER_BOUND,
            CURRENT_TIMESTAMP() as FORECAST_GENERATED_AT
        FROM {database}.ANALYTICS_ML.DELAY_FORECAST_TEMP f
        LEFT JOIN {database}.ANALYTICS_ANALYTICS.ROUTE_PERFORMANCE r 
            ON REPLACE(f.SERIES, '"', '') = r.route_id
        WHERE f.TS >= CURRENT_DATE()
        """
        
        try:
            cursor.execute(insert_sql)
            inserted_count = cursor.rowcount
            print(f"✓ Inserted {inserted_count} delay forecast records")
        except Exception as e:
            print(f"✗ Error inserting delay forecasts: {e}")
        
        # Clean up
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {database}.ANALYTICS_ML.DELAY_FORECAST_TEMP")
        except:
            pass
        
        # Verify
        cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS_ML.DELAY_FORECAST WHERE FORECAST_GENERATED_AT >= DATEADD(hour, -1, CURRENT_TIMESTAMP())")
        final_count = cursor.fetchone()[0]
        print(f"✓ Final delay forecast records: {final_count}")
        
        conn.commit()
        print("✓ Delay forecast model completed successfully")

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
