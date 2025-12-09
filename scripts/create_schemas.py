"""
Create all required schemas in Snowflake
"""
import sys
from pathlib import Path
import os

if os.path.exists('/opt/airflow'):
    project_root = Path('/opt/airflow')
else:
    project_root = Path(__file__).parent.parent

sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config
from api.warehouse_connection import get_warehouse_connection

def create_all_schemas():
    """Create all required schemas"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        print("❌ Only Snowflake is supported")
        return False
    
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    schemas = ['LANDING', 'RAW', 'STAGING', 'TRANSFORM', 'ANALYTICS', 'ML']
    
    try:
        with get_warehouse_connection() as conn:
            cursor = conn.cursor()
            
            print("=" * 80)
            print("CREATING SCHEMAS")
            print("=" * 80)
            
            for schema in schemas:
                try:
                    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}")
                    print(f"✅ Created schema: {database}.{schema}")
                except Exception as e:
                    print(f"⚠️  Schema {schema} may already exist: {e}")
            
            conn.commit()
            print("\n✅ All schemas created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating schemas: {e}")
        return False

if __name__ == "__main__":
    create_all_schemas()

