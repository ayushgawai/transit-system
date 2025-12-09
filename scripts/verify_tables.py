"""
Verify all tables exist in correct schemas and have data
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

def verify_tables():
    """Verify all tables exist in correct schemas"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        print("❌ Only Snowflake is supported")
        return False
    
    sf_config = config.get_snowflake_config()
    database = sf_config.get('database', 'USER_DB_HORNET')
    
    # Expected table structure
    expected_tables = {
        'LANDING': [
            'LANDING_GTFS_STOPS',
            'LANDING_GTFS_ROUTES',
            'LANDING_GTFS_TRIPS',
            'LANDING_GTFS_STOP_TIMES',
            'LANDING_STREAMING_DEPARTURES',
            'GTFS_LOAD_HISTORY'
        ],
        'RAW': [
            'STG_GTFS_STOPS',
            'STG_GTFS_ROUTES',
            'STG_GTFS_TRIPS',
            'STG_GTFS_STOP_TIMES',
            'STG_STREAMING_DEPARTURES'
        ],
        'TRANSFORM': [
            'ROUTE_DEPARTURES'
        ],
        'ANALYTICS': [
            'RELIABILITY_METRICS',
            'DEMAND_METRICS',
            'CROWDING_METRICS',
            'REVENUE_METRICS',
            'DECISION_SUPPORT',
            'ROUTE_PERFORMANCE'
        ],
        'ML': [
            'DEMAND_FORECAST',
            'DELAY_FORECAST'
        ]
    }
    
    try:
        with get_warehouse_connection() as conn:
            cursor = conn.cursor()
            
            print("=" * 80)
            print("TABLE VERIFICATION")
            print("=" * 80)
            print()
            
            all_good = True
            total_tables = 0
            tables_with_data = 0
            
            for schema, tables in expected_tables.items():
                print(f"Schema: {schema}")
                print("-" * 80)
                
                for table in tables:
                    total_tables += 1
                    try:
                        # Check if table exists
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM {database}.INFORMATION_SCHEMA.TABLES
                            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        """, (schema, table))
                        exists = cursor.fetchone()[0] > 0
                        
                        if exists:
                            # Get row count
                            cursor.execute(f"SELECT COUNT(*) FROM {database}.{schema}.{table}")
                            count = cursor.fetchone()[0]
                            
                            if count > 0:
                                print(f"  ✅ {table}: {count:,} rows")
                                tables_with_data += 1
                            else:
                                print(f"  ⚠️  {table}: EXISTS but EMPTY")
                        else:
                            print(f"  ❌ {table}: NOT FOUND")
                            all_good = False
                    except Exception as e:
                        print(f"  ❌ {table}: ERROR - {str(e)[:100]}")
                        all_good = False
                
                print()
            
            print("=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Total tables checked: {total_tables}")
            print(f"Tables with data: {tables_with_data}")
            print(f"All tables exist: {all_good}")
            
            return all_good
            
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

if __name__ == "__main__":
    verify_tables()

