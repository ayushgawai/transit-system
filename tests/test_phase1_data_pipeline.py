#!/usr/bin/env python3
"""
Phase 1 Unit Tests: Data Pipeline
==================================

Tests for:
1. Snowflake connection
2. RAW landing tables exist and have correct schema
3. Data loaded correctly
4. dbt staging models work
5. Snowflake Stream exists
6. Data quality checks

Run with:
    python tests/test_phase1_data_pipeline.py
    
Or with pytest:
    pytest tests/test_phase1_data_pipeline.py -v
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml

try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    print("⚠ snowflake-connector not installed")


# Test Results Tracking
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []
    
    def add(self, name: str, status: str, message: str = ""):
        self.results.append({"name": name, "status": status, "message": message})
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.skipped += 1
    
    def summary(self) -> str:
        return f"PASS: {self.passed} | FAIL: {self.failed} | SKIP: {self.skipped}"


def load_secrets() -> dict:
    """Load secrets from YAML."""
    secrets_path = project_root / "secrets.yaml"
    with open(secrets_path, 'r') as f:
        return yaml.safe_load(f)


def get_connection():
    """Get Snowflake connection."""
    secrets = load_secrets()
    return snowflake.connector.connect(
        account=secrets['SNOWFLAKE_ACCOUNT'],
        user=secrets['SNOWFLAKE_USER'],
        password=secrets['SNOWFLAKE_PASSWORD'],
        warehouse=secrets['SNOWFLAKE_WAREHOUSE'],
        database=secrets['SNOWFLAKE_DATABASE'],
        role=secrets['SNOWFLAKE_ROLE']
    )


# ============================================================================
# TEST SUITE 1: Connection Tests
# ============================================================================

def test_snowflake_connection(results: TestResults):
    """Test 1.1: Snowflake connection works"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_TIMESTAMP()")
        ts = cur.fetchone()[0]
        cur.close()
        conn.close()
        results.add("1.1 Snowflake Connection", "PASS", f"Connected at {ts}")
        return True
    except Exception as e:
        results.add("1.1 Snowflake Connection", "FAIL", str(e))
        return False


def test_warehouse_active(results: TestResults):
    """Test 1.2: Warehouse is active"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_WAREHOUSE()")
        wh = cur.fetchone()[0]
        cur.close()
        conn.close()
        if wh:
            results.add("1.2 Warehouse Active", "PASS", f"Using {wh}")
            return True
        else:
            results.add("1.2 Warehouse Active", "FAIL", "No warehouse selected")
            return False
    except Exception as e:
        results.add("1.2 Warehouse Active", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 2: RAW Tables Exist
# ============================================================================

def test_raw_tables_exist(results: TestResults):
    """Test 2.1: All RAW landing tables exist"""
    required_tables = [
        'TRANSIT_DEPARTURES',
        'TRANSIT_STOPS',
        'TRANSIT_ALERTS',
        'TRANSIT_GTFS_FEEDS',
        'TRANSIT_ROUTES'
    ]
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SHOW TABLES IN SCHEMA RAW")
        tables = [row[1] for row in cur.fetchall()]
        
        missing = [t for t in required_tables if t not in tables]
        
        cur.close()
        conn.close()
        
        if not missing:
            results.add("2.1 RAW Tables Exist", "PASS", f"All {len(required_tables)} tables found")
            return True
        else:
            results.add("2.1 RAW Tables Exist", "FAIL", f"Missing: {missing}")
            return False
    except Exception as e:
        results.add("2.1 RAW Tables Exist", "FAIL", str(e))
        return False


def test_stream_exists(results: TestResults):
    """Test 2.2: Snowflake Stream exists on TRANSIT_DEPARTURES"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SHOW STREAMS IN SCHEMA RAW")
        streams = [row[1] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        if 'TRANSIT_DEPARTURES_STREAM' in streams:
            results.add("2.2 Stream Exists", "PASS", "TRANSIT_DEPARTURES_STREAM found")
            return True
        else:
            results.add("2.2 Stream Exists", "FAIL", f"Stream not found. Found: {streams}")
            return False
    except Exception as e:
        results.add("2.2 Stream Exists", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 3: Data Loaded
# ============================================================================

def test_departures_data_loaded(results: TestResults):
    """Test 3.1: Departures data exists in RAW"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM RAW.TRANSIT_DEPARTURES")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("3.1 Departures Data", "PASS", f"{count} rows in RAW.TRANSIT_DEPARTURES")
            return True
        else:
            results.add("3.1 Departures Data", "FAIL", "No data in RAW.TRANSIT_DEPARTURES")
            return False
    except Exception as e:
        results.add("3.1 Departures Data", "FAIL", str(e))
        return False


def test_stops_data_loaded(results: TestResults):
    """Test 3.2: Stops data exists in RAW"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM RAW.TRANSIT_STOPS")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("3.2 Stops Data", "PASS", f"{count} rows in RAW.TRANSIT_STOPS")
            return True
        else:
            results.add("3.2 Stops Data", "FAIL", "No data in RAW.TRANSIT_STOPS")
            return False
    except Exception as e:
        results.add("3.2 Stops Data", "FAIL", str(e))
        return False


def test_gtfs_data_loaded(results: TestResults):
    """Test 3.3: GTFS data exists in RAW"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM RAW.TRANSIT_GTFS_FEEDS")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("3.3 GTFS Data", "PASS", f"{count} rows in RAW.TRANSIT_GTFS_FEEDS")
            return True
        else:
            results.add("3.3 GTFS Data", "FAIL", "No data in RAW.TRANSIT_GTFS_FEEDS")
            return False
    except Exception as e:
        results.add("3.3 GTFS Data", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 4: dbt Staging Models
# ============================================================================

def test_stg_departures_exists(results: TestResults):
    """Test 4.1: stg_departures table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_STAGING.STG_DEPARTURES")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("4.1 stg_departures", "PASS", f"{count} rows")
            return True
        else:
            results.add("4.1 stg_departures", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("4.1 stg_departures", "FAIL", str(e))
        return False


def test_stg_stops_exists(results: TestResults):
    """Test 4.2: stg_stops table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_STAGING.STG_STOPS")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("4.2 stg_stops", "PASS", f"{count} rows")
            return True
        else:
            results.add("4.2 stg_stops", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("4.2 stg_stops", "FAIL", str(e))
        return False


def test_stg_routes_exists(results: TestResults):
    """Test 4.3: stg_routes table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_STAGING.STG_ROUTES")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("4.3 stg_routes", "PASS", f"{count} rows")
            return True
        else:
            results.add("4.3 stg_routes", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("4.3 stg_routes", "FAIL", str(e))
        return False


def test_stg_alerts_exists(results: TestResults):
    """Test 4.4: stg_alerts table exists"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_STAGING.STG_ALERTS")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        # Alerts might be 0 if no active alerts
        results.add("4.4 stg_alerts", "PASS", f"{count} rows (0 is OK if no alerts)")
        return True
    except Exception as e:
        results.add("4.4 stg_alerts", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 5: Data Quality
# ============================================================================

def test_departures_have_required_fields(results: TestResults):
    """Test 5.1: stg_departures has required fields populated"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(stop_global_id) as has_stop_id,
                COUNT(route_global_id) as has_route_id,
                COUNT(departure_time) as has_departure_time
            FROM STAGING_STAGING.STG_DEPARTURES
        """)
        row = cur.fetchone()
        total, has_stop, has_route, has_time = row
        cur.close()
        conn.close()
        
        if total > 0 and has_stop == total and has_route == total and has_time == total:
            results.add("5.1 Departures Fields", "PASS", f"All {total} rows have required fields")
            return True
        else:
            results.add("5.1 Departures Fields", "FAIL", 
                       f"Missing fields: stop={has_stop}/{total}, route={has_route}/{total}, time={has_time}/{total}")
            return False
    except Exception as e:
        results.add("5.1 Departures Fields", "FAIL", str(e))
        return False


def test_stops_have_coordinates(results: TestResults):
    """Test 5.2: stg_stops has valid coordinates"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN stop_lat BETWEEN -90 AND 90 THEN 1 END) as valid_lat,
                COUNT(CASE WHEN stop_lon BETWEEN -180 AND 180 THEN 1 END) as valid_lon
            FROM STAGING_STAGING.STG_STOPS
        """)
        row = cur.fetchone()
        total, valid_lat, valid_lon = row
        cur.close()
        conn.close()
        
        if total > 0 and valid_lat == total and valid_lon == total:
            results.add("5.2 Stops Coordinates", "PASS", f"All {total} stops have valid coordinates")
            return True
        else:
            results.add("5.2 Stops Coordinates", "FAIL", 
                       f"Invalid coords: lat={valid_lat}/{total}, lon={valid_lon}/{total}")
            return False
    except Exception as e:
        results.add("5.2 Stops Coordinates", "FAIL", str(e))
        return False


def test_delay_status_values(results: TestResults):
    """Test 5.3: delay_status has valid values"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT delay_status 
            FROM STAGING_STAGING.STG_DEPARTURES
            WHERE delay_status IS NOT NULL
        """)
        statuses = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        valid_statuses = {'EARLY', 'ON_TIME', 'LATE', 'VERY_LATE', 'UNKNOWN'}
        invalid = [s for s in statuses if s not in valid_statuses]
        
        if not invalid:
            results.add("5.3 Delay Status Values", "PASS", f"Found: {statuses}")
            return True
        else:
            results.add("5.3 Delay Status Values", "FAIL", f"Invalid values: {invalid}")
            return False
    except Exception as e:
        results.add("5.3 Delay Status Values", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 6: Local Files
# ============================================================================

def test_local_data_files_exist(results: TestResults):
    """Test 6.1: Local test data files exist"""
    data_dir = project_root / "ingestion" / "data" / "local_test"
    
    departures = list((data_dir / "transitapp" / "departures").rglob("*.json")) if (data_dir / "transitapp" / "departures").exists() else []
    stops = list((data_dir / "transitapp" / "stops").rglob("*.json")) if (data_dir / "transitapp" / "stops").exists() else []
    gtfs = list((data_dir / "gtfs").rglob("*.zip")) if (data_dir / "gtfs").exists() else []
    
    if departures and stops and gtfs:
        results.add("6.1 Local Data Files", "PASS", 
                   f"departures={len(departures)}, stops={len(stops)}, gtfs={len(gtfs)}")
        return True
    else:
        results.add("6.1 Local Data Files", "FAIL", 
                   f"departures={len(departures)}, stops={len(stops)}, gtfs={len(gtfs)}")
        return False


def test_data_loader_script_exists(results: TestResults):
    """Test 6.2: Data loader script exists"""
    script_path = project_root / "scripts" / "load_data_to_snowflake.py"
    
    if script_path.exists():
        results.add("6.2 Data Loader Script", "PASS", str(script_path))
        return True
    else:
        results.add("6.2 Data Loader Script", "FAIL", "Script not found")
        return False


def test_kafka_files_exist(results: TestResults):
    """Test 6.3: Kafka setup files exist"""
    kafka_dir = project_root / "kafka"
    required = ["docker-compose.yml", "transit_producer.py", "transit_consumer.py"]
    
    missing = [f for f in required if not (kafka_dir / f).exists()]
    
    if not missing:
        results.add("6.3 Kafka Files", "PASS", f"All {len(required)} files found")
        return True
    else:
        results.add("6.3 Kafka Files", "FAIL", f"Missing: {missing}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all Phase 1 tests."""
    print("=" * 70)
    print("PHASE 1 UNIT TESTS: Data Pipeline")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = TestResults()
    
    # Suite 1: Connection
    print("📡 Suite 1: Connection Tests")
    print("-" * 40)
    if not SNOWFLAKE_AVAILABLE:
        results.add("1.x Connection Tests", "SKIP", "snowflake-connector not installed")
        print("  ⚠ SKIPPED - snowflake-connector not installed")
    else:
        test_snowflake_connection(results)
        test_warehouse_active(results)
    print()
    
    # Suite 2: RAW Tables
    print("📦 Suite 2: RAW Tables")
    print("-" * 40)
    if SNOWFLAKE_AVAILABLE:
        test_raw_tables_exist(results)
        test_stream_exists(results)
    else:
        results.add("2.x RAW Tables", "SKIP", "No Snowflake connection")
    print()
    
    # Suite 3: Data Loaded
    print("📊 Suite 3: Data Loaded")
    print("-" * 40)
    if SNOWFLAKE_AVAILABLE:
        test_departures_data_loaded(results)
        test_stops_data_loaded(results)
        test_gtfs_data_loaded(results)
    else:
        results.add("3.x Data Loaded", "SKIP", "No Snowflake connection")
    print()
    
    # Suite 4: dbt Staging
    print("🔄 Suite 4: dbt Staging Models")
    print("-" * 40)
    if SNOWFLAKE_AVAILABLE:
        test_stg_departures_exists(results)
        test_stg_stops_exists(results)
        test_stg_routes_exists(results)
        test_stg_alerts_exists(results)
    else:
        results.add("4.x Staging Models", "SKIP", "No Snowflake connection")
    print()
    
    # Suite 5: Data Quality
    print("✅ Suite 5: Data Quality")
    print("-" * 40)
    if SNOWFLAKE_AVAILABLE:
        test_departures_have_required_fields(results)
        test_stops_have_coordinates(results)
        test_delay_status_values(results)
    else:
        results.add("5.x Data Quality", "SKIP", "No Snowflake connection")
    print()
    
    # Suite 6: Local Files
    print("📁 Suite 6: Local Files")
    print("-" * 40)
    test_local_data_files_exist(results)
    test_data_loader_script_exists(results)
    test_kafka_files_exist(results)
    print()
    
    # Print Results
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    for r in results.results:
        icon = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⚠️"
        print(f"  {icon} {r['name']}: {r['status']}")
        if r["message"]:
            print(f"      └─ {r['message']}")
    
    print()
    print("-" * 70)
    print(f"SUMMARY: {results.summary()}")
    print("-" * 70)
    
    if results.failed == 0:
        print("\n🎉 ALL TESTS PASSED! Phase 1 is complete.")
        print("   Ready to proceed to Phase 2.")
        return 0
    else:
        print(f"\n⚠️  {results.failed} test(s) failed. Please fix before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

