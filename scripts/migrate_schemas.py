"""
Schema Migration Script
Moves tables to proper schemas and updates all references
"""
import sys
from pathlib import Path
import os
from datetime import datetime

if os.path.exists('/opt/airflow'):
    project_root = Path('/opt/airflow')
else:
    project_root = Path(__file__).parent.parent

sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config
from api.warehouse_connection import get_warehouse_connection

def create_schemas():
    """Create all required schemas"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        raise ValueError("Only Snowflake is supported")
    
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    schemas = ['LANDING', 'RAW', 'STAGING', 'TRANSFORM', 'ANALYTICS', 'ML']
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        
        print("Creating schemas...")
        for schema in schemas:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}")
            print(f"  ✓ Created schema: {schema}")
        
        # Create backup schema
        backup_schema = f"BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.{backup_schema}")
        print(f"  ✓ Created backup schema: {backup_schema}")
        
        conn.commit()
        return backup_schema

def list_current_tables():
    """List all tables in ANALYTICS schema (where they shouldn't be)"""
    config = get_warehouse_config()
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        
        # Get all tables in ANALYTICS schema
        cursor.execute(f"""
            SELECT TABLE_NAME, TABLE_TYPE
            FROM {database}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ANALYTICS'
            ORDER BY TABLE_NAME
        """)
        return cursor.fetchall()

def migrate_table(database, source_schema, target_schema, table_name, backup_schema):
    """Move a table from source to target schema with backup"""
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Create backup
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {database}.{backup_schema}.{table_name} 
                AS SELECT * FROM {database}.{source_schema}.{table_name}
            """)
            
            # Move table (rename)
            cursor.execute(f"""
                ALTER TABLE {database}.{source_schema}.{table_name}
                RENAME TO {database}.{target_schema}.{table_name}
            """)
            
            conn.commit()
            print(f"  ✓ Moved {source_schema}.{table_name} -> {target_schema}.{table_name}")
            return True
        except Exception as e:
            print(f"  ✗ Error moving {source_schema}.{table_name}: {e}")
            conn.rollback()
            return False

def main():
    """Main migration function"""
    print("=" * 80)
    print("SCHEMA MIGRATION SCRIPT")
    print("=" * 80)
    print()
    
    # Create schemas
    backup_schema = create_schemas()
    print()
    
    # List current tables
    print("Current tables in ANALYTICS schema:")
    tables = list_current_tables()
    for table_name, table_type in tables:
        print(f"  {table_type:15} {table_name}")
    print()
    
    # Define table migrations
    config = get_warehouse_config()
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    migrations = [
        # Landing tables (from ANALYTICS to LANDING)
        ('ANALYTICS', 'LANDING', 'LANDING_GTFS_STOPS'),
        ('ANALYTICS', 'LANDING', 'LANDING_GTFS_ROUTES'),
        ('ANALYTICS', 'LANDING', 'LANDING_GTFS_TRIPS'),
        ('ANALYTICS', 'LANDING', 'LANDING_GTFS_STOP_TIMES'),
        ('ANALYTICS', 'LANDING', 'LANDING_STREAMING_DEPARTURES'),
        ('ANALYTICS', 'LANDING', 'GTFS_LOAD_HISTORY'),
        
        # Staging tables (from ANALYTICS to RAW)
        ('ANALYTICS', 'RAW', 'STG_GTFS_STOPS'),
        ('ANALYTICS', 'RAW', 'STG_GTFS_ROUTES'),
        ('ANALYTICS', 'RAW', 'STG_GTFS_TRIPS'),
        ('ANALYTICS', 'RAW', 'STG_GTFS_STOP_TIMES'),
        ('ANALYTICS', 'RAW', 'STG_STREAMING_DEPARTURES'),
    ]
    
    print("Migrating tables...")
    success_count = 0
    for source_schema, target_schema, table_name in migrations:
        if migrate_table(database, source_schema, target_schema, table_name, backup_schema):
            success_count += 1
    
    print()
    print(f"Migration complete: {success_count}/{len(migrations)} tables migrated")
    print(f"Backup schema: {database}.{backup_schema}")

if __name__ == "__main__":
    main()

