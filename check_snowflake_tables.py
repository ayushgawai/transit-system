#!/usr/bin/env python3
"""
Script to check Snowflake tables and schemas
"""
import boto3
import json
import snowflake.connector
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config

def main():
    print("=" * 70)
    print("🔍 CHECKING SNOWFLAKE TABLES & SCHEMAS")
    print("=" * 70)
    print()
    
    try:
        config = get_warehouse_config()
        snowflake_config = config.get_snowflake_config()
        
        print("📋 Connection Details:")
        print(f"   Account: {snowflake_config.get('account', 'N/A')}")
        print(f"   User: {snowflake_config.get('user', 'N/A')}")
        print(f"   Database: {snowflake_config.get('database', 'N/A')}")
        print(f"   Warehouse: {snowflake_config.get('warehouse', 'N/A')}")
        print()
        
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            account=snowflake_config.get('account'),
            user=snowflake_config.get('user'),
            password=snowflake_config.get('password'),
            warehouse=snowflake_config.get('warehouse', 'HORNET_QUERY_WH'),
            database=snowflake_config.get('database', 'USER_DB_HORNET'),
            role=snowflake_config.get('role', 'TRAINING_ROLE')
        )
        
        cursor = conn.cursor()
        database = snowflake_config.get('database', 'USER_DB_HORNET')
        
        print("=" * 70)
        print("📊 AVAILABLE SCHEMAS")
        print("=" * 70)
        cursor.execute(f"SHOW SCHEMAS IN DATABASE {database}")
        schemas = cursor.fetchall()
        for schema in schemas:
            schema_name = schema[1] if len(schema) > 1 else schema[0]
            print(f"   • {database}.{schema_name}")
        print()
        
        # Check each schema for tables
        important_schemas = ['STAGING', 'ANALYTICS', 'LANDING', 'RAW']
        
        for schema_name in important_schemas:
            print("=" * 70)
            print(f"📋 TABLES IN {database}.{schema_name}")
            print("=" * 70)
            try:
                cursor.execute(f"SHOW TABLES IN SCHEMA {database}.{schema_name}")
                tables = cursor.fetchall()
                if tables:
                    for table in tables:
                        table_name = table[1] if len(table) > 1 else table[0]
                        # Get row count
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {database}.{schema_name}.{table_name}")
                            count = cursor.fetchone()[0]
                            print(f"   ✅ {table_name}: {count:,} rows")
                        except Exception as e:
                            print(f"   ⚠️  {table_name}: Error getting count - {str(e)[:50]}")
                else:
                    print(f"   ⚠️  No tables found in {schema_name}")
            except Exception as e:
                print(f"   ❌ Error accessing {schema_name}: {str(e)[:100]}")
            print()
        
        # Check specific tables we use
        print("=" * 70)
        print("🔍 CHECKING SPECIFIC TABLES WE USE")
        print("=" * 70)
        
        tables_to_check = [
            (database, 'STAGING', 'STG_STOPS'),
            (database, 'STAGING', 'STG_ROUTES'),
            (database, 'STAGING', 'STG_DEPARTURES'),
            (database, 'ANALYTICS', 'RELIABILITY_METRICS'),
            (database, 'ANALYTICS', 'CROWDING_METRICS'),
            (database, 'LANDING', 'LANDING_STREAMING_DEPARTURES'),
        ]
        
        for db, schema, table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {db}.{schema}.{table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {db}.{schema}.{table}: {count:,} rows")
                
                # Get column names
                cursor.execute(f"DESCRIBE TABLE {db}.{schema}.{table}")
                columns = cursor.fetchall()
                col_names = [col[0] for col in columns]
                print(f"      Columns: {', '.join(col_names[:10])}{'...' if len(col_names) > 10 else ''}")
            except Exception as e:
                print(f"   ❌ {db}.{schema}.{table}: {str(e)[:80]}")
        print()
        
        # Check for streaming data
        print("=" * 70)
        print("🌊 CHECKING STREAMING DATA")
        print("=" * 70)
        try:
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN LOAD_TIMESTAMP >= DATEADD(hour, -1, CURRENT_TIMESTAMP()) THEN 1 END) as last_hour,
                    MAX(LOAD_TIMESTAMP) as latest_timestamp
                FROM {database}.LANDING.LANDING_STREAMING_DEPARTURES
            """)
            row = cursor.fetchone()
            if row:
                print(f"   Total records: {row[0]:,}")
                print(f"   Last hour: {row[1]:,}")
                print(f"   Latest timestamp: {row[2]}")
                if row[1] > 0:
                    print("   ✅ Streaming is ACTIVE")
                else:
                    print("   ⚠️  Streaming is INACTIVE (no data in last hour)")
        except Exception as e:
            print(f"   ❌ Error checking streaming: {str(e)[:80]}")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 70)
        print("✅ SNOWFLAKE CHECK COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

