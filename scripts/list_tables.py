"""
List all tables in Snowflake with their schemas
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

def list_all_tables():
    """List all tables in all schemas"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        print("Only Snowflake is supported")
        return
    
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        
        # Get all schemas
        cursor.execute(f"""
            SELECT SCHEMA_NAME 
            FROM {database}.INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA')
            ORDER BY SCHEMA_NAME
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        
        print("=" * 80)
        print("CURRENT SCHEMA STRUCTURE IN SNOWFLAKE")
        print("=" * 80)
        print()
        
        all_tables = {}
        
        for schema in schemas:
            cursor.execute(f"""
                SELECT TABLE_NAME, TABLE_TYPE
                FROM {database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
            """, (schema,))
            tables = cursor.fetchall()
            
            if tables:
                all_tables[schema] = tables
                print(f"SCHEMA: {schema}")
                print("-" * 80)
                for table_name, table_type in tables:
                    print(f"  {table_type:15} {table_name}")
                print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for schema, tables in all_tables.items():
            print(f"{schema}: {len(tables)} tables")
        
        return all_tables

if __name__ == "__main__":
    list_all_tables()

