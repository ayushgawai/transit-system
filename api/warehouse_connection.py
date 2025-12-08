"""
Warehouse Connection Manager
Handles connections to Redshift or Snowflake based on config
"""
from contextlib import contextmanager
from typing import Any
from config.warehouse_config import get_warehouse_config

def get_warehouse_connection():
    """Get warehouse connection based on config (Snowflake only)"""
    return get_snowflake_connection()

@contextmanager
def get_snowflake_connection():
    """Context manager for Snowflake connections"""
    import snowflake.connector
    config = get_warehouse_config()
    snowflake_config = config.get_snowflake_config()
    
    if not snowflake_config.get('account'):
        raise ConnectionError("Snowflake account not configured. Please update config.yaml or AWS Secrets Manager.")
    
    database = snowflake_config.get('database', 'USER_DB_HORNET')
    schema = snowflake_config.get('schema', 'STAGING')
    
    conn = snowflake.connector.connect(
        account=snowflake_config.get('account'),
        user=snowflake_config.get('user'),
        password=snowflake_config.get('password'),
        warehouse=snowflake_config.get('warehouse', 'HORNET_QUERY_WH'),
        database=database,
        role=snowflake_config.get('role', 'TRAINING_ROLE')
    )
    
    try:
        # Set schema context
        cursor = conn.cursor()
        cursor.execute(f"USE DATABASE {database}")
        cursor.close()
        yield conn
    finally:
        conn.close()

