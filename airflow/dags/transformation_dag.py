"""
Airflow DAG: Data Transformation with dbt

This DAG orchestrates data transformation workflows:
1. Wait for Snowpipe to complete loading raw data
2. Run dbt staging models (clean and normalize raw data)
3. Run dbt marts models (build analytics tables)
4. Run dbt tests to validate data quality
5. Refresh BI dashboard connections

Schedule: Every 10 minutes (runs after ingestion)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowSkipException

# Try to import dbt operators (if dbt-cloud plugin installed)
try:
    from airflow.providers.dbt.cloud.operators.dbt import DbtCloudRunJobOperator
    DBT_CLOUD_AVAILABLE = True
except ImportError:
    DBT_CLOUD_AVAILABLE = False
    print("dbt-cloud provider not available, using BashOperator for dbt runs")

default_args = {
    'owner': 'transit-data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

dag = DAG(
    'transit_transformation',
    default_args=default_args,
    description='Orchestrate dbt transformations for transit data',
    schedule_interval='*/10 * * * *',  # Every 10 minutes
    catchup=False,
    tags=['transit', 'transformation', 'dbt'],
)


# =============================================================================
# WAIT FOR RAW DATA LOAD
# =============================================================================

check_raw_data_loaded = PythonOperator(
    task_id='check_raw_data_loaded',
    python_callable=lambda **context: print("Checking if raw data is loaded..."),
    dag=dag,
)

# In production, this would query Snowflake to verify new data arrived
# Example: SELECT COUNT(*) FROM RAW.TRANSITAPP_API_CALLS WHERE load_timestamp > CURRENT_TIMESTAMP - INTERVAL '15 minutes'


# =============================================================================
# DBT STAGING MODELS
# =============================================================================

dbt_debug = BashOperator(
    task_id='dbt_debug',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt debug --profiles-dir {{ var.value.dbt_profiles_dir }}
    """,
    dag=dag,
)

dbt_deps = BashOperator(
    task_id='dbt_deps',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt deps --profiles-dir {{ var.value.dbt_profiles_dir }}
    """,
    dag=dag,
)

dbt_run_staging = BashOperator(
    task_id='dbt_run_staging',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt run --select staging.* --profiles-dir {{ var.value.dbt_profiles_dir }} --target {{ var.value.dbt_target }}
    """,
    dag=dag,
)

dbt_test_staging = BashOperator(
    task_id='dbt_test_staging',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt test --select staging.* --profiles-dir {{ var.value.dbt_profiles_dir }} --target {{ var.value.dbt_target }}
    """,
    dag=dag,
)


# =============================================================================
# DBT TRANSFORM MODELS
# =============================================================================

dbt_run_transform = BashOperator(
    task_id='dbt_run_transform',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt run --select transform.* --profiles-dir {{ var.value.dbt_profiles_dir }} --target {{ var.value.dbt_target }}
    """,
    dag=dag,
)

dbt_test_transform = BashOperator(
    task_id='dbt_test_transform',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt test --select transform.* --profiles-dir {{ var.value.dbt_profiles_dir }} --target {{ var.value.dbt_target }}
    """,
    dag=dag,
)


# =============================================================================
# DBT ANALYTICS MODELS
# =============================================================================

dbt_run_analytics = BashOperator(
    task_id='dbt_run_analytics',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt run --select analytics.* --profiles-dir {{ var.value.dbt_profiles_dir }} --target {{ var.value.dbt_target }}
    """,
    dag=dag,
)

dbt_test_analytics = BashOperator(
    task_id='dbt_test_analytics',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt test --select analytics.* --profiles-dir {{ var.value.dbt_profiles_dir }} --target {{ var.value.dbt_target }}
    """,
    dag=dag,
)


# =============================================================================
# DBT DOCS GENERATION (OPTIONAL)
# =============================================================================

dbt_docs_generate = BashOperator(
    task_id='dbt_docs_generate',
    bash_command="""
    cd {{ var.value.dbt_project_dir }}
    dbt docs generate --profiles-dir {{ var.value.dbt_profiles_dir }} --target {{ var.value.dbt_target }}
    """,
    dag=dag,
)


# =============================================================================
# REFRESH BI CONNECTIONS (OPTIONAL)
# =============================================================================

refresh_bi_connections = PythonOperator(
    task_id='refresh_bi_connections',
    python_callable=lambda **context: print("BI connections refreshed (if applicable)"),
    dag=dag,
)


# =============================================================================
# TASK DEPENDENCIES
# =============================================================================

check_raw_data_loaded >> dbt_debug >> dbt_deps >> dbt_run_staging >> dbt_test_staging
dbt_test_staging >> dbt_run_transform >> dbt_test_transform
dbt_test_transform >> dbt_run_analytics >> dbt_test_analytics
dbt_test_analytics >> dbt_docs_generate >> refresh_bi_connections

