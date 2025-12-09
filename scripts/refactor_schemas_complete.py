"""
Complete Schema Refactoring Script
This script will:
1. Create proper schemas (LANDING, RAW, STAGING, TRANSFORM, ANALYTICS, ML)
2. Backup existing tables
3. Move tables to correct schemas
4. Update all references in code
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

print("=" * 80)
print("SCHEMA REFACTORING PLAN")
print("=" * 80)
print()
print("SCHEMA STRUCTURE:")
print("  LANDING   - Raw data from APIs/GTFS (initial ingestion)")
print("  RAW       - Cleaned raw data (from dbt staging models: stg_*)")
print("  STAGING   - Staging views/models (dbt staging)")
print("  TRANSFORM - Intermediate transformations (dbt transform)")
print("  ANALYTICS - Final analytics tables (dbt analytics)")
print("  ML        - ML models and forecasts (dbt ml_forecasts)")
print()
print("TABLES TO MIGRATE:")
print()
print("LANDING schema:")
print("  - LANDING_GTFS_STOPS")
print("  - LANDING_GTFS_ROUTES")
print("  - LANDING_GTFS_TRIPS")
print("  - LANDING_GTFS_STOP_TIMES")
print("  - LANDING_STREAMING_DEPARTURES")
print("  - GTFS_LOAD_HISTORY")
print()
print("RAW schema (from dbt landing_to_raw models):")
print("  - STG_GTFS_STOPS")
print("  - STG_GTFS_ROUTES")
print("  - STG_GTFS_TRIPS")
print("  - STG_GTFS_STOP_TIMES")
print()
print("RAW schema (from dbt streaming_to_analytics models):")
print("  - STG_STREAMING_DEPARTURES")
print()
print("ANALYTICS schema (from dbt analytics models):")
print("  - RELIABILITY_METRICS")
print("  - DEMAND_METRICS")
print("  - CROWDING_METRICS")
print("  - REVENUE_METRICS")
print("  - DECISION_SUPPORT")
print("  - ROUTE_PERFORMANCE")
print()
print("ML schema (from dbt ml_forecasts models):")
print("  - DEMAND_FORECAST")
print("  - DELAY_FORECAST")
print()
print("=" * 80)
print("FILES TO UPDATE:")
print("=" * 80)
print("1. ingestion/fetch_gtfs_incremental.py - Use LANDING schema")
print("2. ingestion/transit_streaming_producer.py - Use LANDING schema")
print("3. ingestion/kafka_consumer_to_landing.py - Use LANDING schema")
print("4. dbt/transit_dbt/models/sources.yml - Point to LANDING schema")
print("5. dbt/transit_dbt/dbt_project.yml - Update schema configs")
print("6. api/main.py - Update all schema references")
print("7. api/llm/chat_handler.py - Update schema references")
print("8. airflow/dags/*.py - Update schema references")
print()
print("=" * 80)
print("NEXT: Run migration script after reviewing this plan")
print("=" * 80)

