"""
Airflow DAG: ML Model Refresh

This DAG orchestrates ML model training and prediction workflows:
1. Train/retrain demand forecasting model
2. Train/retrain delay forecasting model
3. Train/retrain crowding forecasting model
4. Generate predictions for next 24-48 hours
5. Write predictions to forecasts marts

Schedule: Daily at 3 AM UTC (after transformations complete)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'transit-data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
    'start_date': days_ago(1),
}

dag = DAG(
    'transit_ml_refresh',
    default_args=default_args,
    description='Orchestrate ML model training and predictions for transit data',
    schedule_interval='0 3 * * *',  # Daily at 3 AM UTC
    catchup=False,
    tags=['transit', 'ml', 'forecasting'],
)


# =============================================================================
# CHECK DATA AVAILABILITY
# =============================================================================

check_data_availability = SnowflakeOperator(
    task_id='check_data_availability',
    snowflake_conn_id='snowflake_default',
    sql="""
    -- Check that sufficient data exists for training
    SELECT 
        COUNT(*) as record_count,
        MIN(timestamp) as min_timestamp,
        MAX(timestamp) as max_timestamp
    FROM STAGING.DEPARTURES
    WHERE timestamp >= CURRENT_DATE - 30
    """,
    dag=dag,
)


# =============================================================================
# DEMAND FORECASTING MODEL
# =============================================================================

train_demand_model = SnowflakeOperator(
    task_id='train_demand_forecast_model',
    snowflake_conn_id='snowflake_default',
    sql="""
    -- Train demand forecasting model using Snowflake ML
    -- This is a placeholder - actual implementation would use Snowpark ML or stored procedures
    CALL TRAIN_DEMAND_FORECAST_MODEL();
    """,
    dag=dag,
)

generate_demand_forecasts = SnowflakeOperator(
    task_id='generate_demand_forecasts',
    snowflake_conn_id='snowflake_default',
    sql="""
    -- Generate demand forecasts for next 24 hours
    CALL GENERATE_DEMAND_FORECASTS(
        forecast_horizon_hours => 24,
        prediction_interval => 'hourly'
    );
    """,
    dag=dag,
)


# =============================================================================
# DELAY FORECASTING MODEL
# =============================================================================

train_delay_model = SnowflakeOperator(
    task_id='train_delay_forecast_model',
    snowflake_conn_id='snowflake_default',
    sql="""
    CALL TRAIN_DELAY_FORECAST_MODEL();
    """,
    dag=dag,
)

generate_delay_forecasts = SnowflakeOperator(
    task_id='generate_delay_forecasts',
    snowflake_conn_id='snowflake_default',
    sql="""
    -- Generate delay forecasts for next 48 hours
    CALL GENERATE_DELAY_FORECASTS(
        forecast_horizon_hours => 48,
        prediction_interval => 'hourly'
    );
    """,
    dag=dag,
)


# =============================================================================
# CROWDING FORECASTING MODEL
# =============================================================================

train_crowding_model = SnowflakeOperator(
    task_id='train_crowding_forecast_model',
    snowflake_conn_id='snowflake_default',
    sql="""
    CALL TRAIN_CROWDING_FORECAST_MODEL();
    """,
    dag=dag,
)

generate_crowding_forecasts = SnowflakeOperator(
    task_id='generate_crowding_forecasts',
    snowflake_conn_id='snowflake_default',
    sql="""
    -- Generate crowding forecasts for next 24 hours
    CALL GENERATE_CROWDING_FORECASTS(
        forecast_horizon_hours => 24,
        prediction_interval => 'hourly'
    );
    """,
    dag=dag,
)


# =============================================================================
# VALIDATE FORECASTS
# =============================================================================

validate_forecasts = SnowflakeOperator(
    task_id='validate_forecasts',
    snowflake_conn_id='snowflake_default',
    sql="""
    -- Validate that forecasts were generated successfully
    SELECT 
        COUNT(*) as forecast_count,
        MIN(forecast_timestamp) as min_forecast,
        MAX(forecast_timestamp) as max_forecast
    FROM ANALYTICS.DECISION_SUPPORT
    WHERE created_at >= CURRENT_DATE;
    
    -- Alert if insufficient forecasts
    -- In production, use Airflow XComs to check results and fail if needed
    """,
    dag=dag,
)


# =============================================================================
# UPDATE DECISION SUPPORT TABLES
# =============================================================================

refresh_decision_support = SnowflakeOperator(
    task_id='refresh_decision_support',
    snowflake_conn_id='snowflake_default',
    sql="""
    -- Refresh decision support recommendations based on forecasts and historical data
    CALL REFRESH_DECISION_SUPPORT();
    """,
    dag=dag,
)


# =============================================================================
# TASK DEPENDENCIES
# =============================================================================

check_data_availability >> [
    train_demand_model,
    train_delay_model,
    train_crowding_model
]

train_demand_model >> generate_demand_forecasts
train_delay_model >> generate_delay_forecasts
train_crowding_model >> generate_crowding_forecasts

[generate_demand_forecasts, generate_delay_forecasts, generate_crowding_forecasts] >> validate_forecasts
validate_forecasts >> refresh_decision_support

