#!/usr/bin/env python3
"""
Load Local Test Data to Snowflake

This script loads transit data from local JSON files into Snowflake RAW tables.
It's designed for local development and testing before AWS deployment.

Usage:
    python scripts/load_data_to_snowflake.py [--all] [--departures] [--stops] [--gtfs]
    
Options:
    --all        Load all data types (default)
    --departures Load only departure data
    --stops      Load only stops data
    --gtfs       Load only GTFS data
    --dry-run    Show what would be loaded without actually loading
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import zipfile
import csv
import io

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import snowflake.connector
import yaml


def load_secrets(secrets_path: str = "secrets.yaml") -> dict:
    """Load secrets from YAML file."""
    full_path = project_root / secrets_path
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)


def get_snowflake_connection(secrets: dict):
    """Create Snowflake connection from secrets."""
    return snowflake.connector.connect(
        account=secrets['SNOWFLAKE_ACCOUNT'],
        user=secrets['SNOWFLAKE_USER'],
        password=secrets['SNOWFLAKE_PASSWORD'],
        warehouse=secrets['SNOWFLAKE_WAREHOUSE'],
        database=secrets['SNOWFLAKE_DATABASE'],
        role=secrets['SNOWFLAKE_ROLE']
    )


def find_json_files(base_path: Path, pattern: str = "*.json") -> list:
    """Find all JSON files matching pattern."""
    return list(base_path.rglob(pattern))


def load_departures(conn, data_dir: Path, dry_run: bool = False) -> int:
    """Load departure JSON files into RAW.TRANSIT_DEPARTURES."""
    departures_dir = data_dir / "transitapp" / "departures"
    if not departures_dir.exists():
        print(f"  ⚠ Departures directory not found: {departures_dir}")
        return 0
    
    json_files = find_json_files(departures_dir, "departures_*.json")
    print(f"  Found {len(json_files)} departure files")
    
    if dry_run:
        for f in json_files[:5]:
            print(f"    Would load: {f}")
        return len(json_files)
    
    cursor = conn.cursor()
    loaded = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract metadata
            source_file = str(json_file.relative_to(project_root))
            timestamp = data.get('timestamp', datetime.utcnow().isoformat())
            stop = data.get('stop', {})
            stop_global_id = stop.get('global_stop_id', '')
            stop_name = stop.get('stop_name', '')
            
            # Convert to JSON string for VARIANT column
            raw_json = json.dumps(data)
            
            # Insert into Snowflake
            cursor.execute("""
                INSERT INTO RAW.TRANSIT_DEPARTURES 
                (source_file, raw_json, stop_global_id, stop_name, fetch_timestamp)
                SELECT 
                    %s,
                    PARSE_JSON(%s),
                    %s,
                    %s,
                    TRY_TO_TIMESTAMP_NTZ(%s)
            """, (source_file, raw_json, stop_global_id, stop_name, timestamp))
            
            loaded += 1
            
        except Exception as e:
            print(f"    ✗ Error loading {json_file}: {e}")
    
    cursor.close()
    print(f"  ✓ Loaded {loaded} departure files")
    return loaded


def load_stops(conn, data_dir: Path, dry_run: bool = False) -> int:
    """Load stops JSON files into RAW.TRANSIT_STOPS."""
    stops_dir = data_dir / "transitapp" / "stops"
    if not stops_dir.exists():
        print(f"  ⚠ Stops directory not found: {stops_dir}")
        return 0
    
    json_files = find_json_files(stops_dir, "stops_*.json")
    print(f"  Found {len(json_files)} stops files")
    
    if dry_run:
        for f in json_files[:5]:
            print(f"    Would load: {f}")
        return len(json_files)
    
    cursor = conn.cursor()
    loaded = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            source_file = str(json_file.relative_to(project_root))
            location = data.get('location', {})
            location_lat = location.get('lat', 0)
            location_lon = location.get('lon', 0)
            stops = data.get('stops', [])
            stops_count = len(stops)
            
            # Wrap in expected format
            raw_data = {'stops': stops}
            raw_json = json.dumps(raw_data)
            
            cursor.execute("""
                INSERT INTO RAW.TRANSIT_STOPS 
                (source_file, raw_json, location_lat, location_lon, stops_count, fetch_timestamp)
                SELECT 
                    %s,
                    PARSE_JSON(%s),
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP()
            """, (source_file, raw_json, location_lat, location_lon, stops_count))
            
            loaded += 1
            
        except Exception as e:
            print(f"    ✗ Error loading {json_file}: {e}")
    
    cursor.close()
    print(f"  ✓ Loaded {loaded} stops files")
    return loaded


def load_gtfs(conn, data_dir: Path, dry_run: bool = False) -> int:
    """Load GTFS zip files into RAW.TRANSIT_GTFS_FEEDS."""
    gtfs_dir = data_dir / "gtfs"
    if not gtfs_dir.exists():
        print(f"  ⚠ GTFS directory not found: {gtfs_dir}")
        return 0
    
    zip_files = list(gtfs_dir.rglob("*.zip"))
    print(f"  Found {len(zip_files)} GTFS zip files")
    
    if dry_run:
        for f in zip_files[:3]:
            print(f"    Would load: {f}")
        return len(zip_files)
    
    cursor = conn.cursor()
    loaded = 0
    
    for zip_file in zip_files:
        try:
            # Extract agency from path (e.g., gtfs/BART/raw/...)
            parts = zip_file.parts
            agency = "UNKNOWN"
            for i, part in enumerate(parts):
                if part == "gtfs" and i + 1 < len(parts):
                    agency = parts[i + 1]
                    break
            
            source_file = str(zip_file.relative_to(project_root))
            file_size = zip_file.stat().st_size
            
            # Parse GTFS files from zip
            gtfs_data = parse_gtfs_zip(zip_file)
            
            cursor.execute("""
                INSERT INTO RAW.TRANSIT_GTFS_FEEDS 
                (source_file, agency, feed_url, file_size_bytes, 
                 gtfs_routes, gtfs_stops, gtfs_trips, gtfs_stop_times, gtfs_calendar)
                SELECT 
                    %s, %s, %s, %s,
                    PARSE_JSON(%s),
                    PARSE_JSON(%s),
                    PARSE_JSON(%s),
                    PARSE_JSON(%s),
                    PARSE_JSON(%s)
            """, (
                source_file, agency, '', file_size,
                json.dumps(gtfs_data.get('routes', [])),
                json.dumps(gtfs_data.get('stops', [])),
                json.dumps(gtfs_data.get('trips', [])),
                json.dumps(gtfs_data.get('stop_times', [])[:1000]),  # Limit stop_times (can be huge)
                json.dumps(gtfs_data.get('calendar', []))
            ))
            
            loaded += 1
            
        except Exception as e:
            print(f"    ✗ Error loading {zip_file}: {e}")
    
    cursor.close()
    print(f"  ✓ Loaded {loaded} GTFS feeds")
    return loaded


def parse_gtfs_zip(zip_path: Path) -> dict:
    """Parse GTFS zip file and extract key tables as lists of dicts."""
    gtfs_data = {}
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files_to_parse = {
                'routes.txt': 'routes',
                'stops.txt': 'stops',
                'trips.txt': 'trips',
                'stop_times.txt': 'stop_times',
                'calendar.txt': 'calendar'
            }
            
            for filename, key in files_to_parse.items():
                try:
                    with zf.open(filename) as f:
                        content = f.read().decode('utf-8-sig')  # Handle BOM
                        reader = csv.DictReader(io.StringIO(content))
                        gtfs_data[key] = list(reader)
                except KeyError:
                    # File not in zip
                    gtfs_data[key] = []
                except Exception as e:
                    print(f"      Warning: Could not parse {filename}: {e}")
                    gtfs_data[key] = []
    
    except Exception as e:
        print(f"    Error parsing zip: {e}")
    
    return gtfs_data


def create_tables_if_not_exist(conn):
    """Ensure landing tables exist."""
    cursor = conn.cursor()
    
    # Read and execute SQL file
    sql_file = project_root / "snowflake" / "setup" / "01_landing_tables.sql"
    if sql_file.exists():
        print("Creating/verifying landing tables...")
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        for stmt in statements:
            # Skip comments-only statements
            if stmt.startswith('--') and '\n' not in stmt:
                continue
            try:
                cursor.execute(stmt)
            except Exception as e:
                # Ignore "already exists" errors
                if "already exists" not in str(e).lower():
                    print(f"  Warning: {e}")
        
        print("  ✓ Tables verified/created")
    else:
        print(f"  ⚠ SQL file not found: {sql_file}")
    
    cursor.close()


def show_table_counts(conn):
    """Show row counts for all transit tables."""
    cursor = conn.cursor()
    
    tables = [
        'RAW.TRANSIT_DEPARTURES',
        'RAW.TRANSIT_STOPS',
        'RAW.TRANSIT_ALERTS',
        'RAW.TRANSIT_GTFS_FEEDS',
        'RAW.TRANSIT_ROUTES'
    ]
    
    print("\n📊 Table Row Counts:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")
        except Exception as e:
            print(f"  {table}: (not found or error)")
    
    cursor.close()


def main():
    parser = argparse.ArgumentParser(description='Load transit data to Snowflake')
    parser.add_argument('--all', action='store_true', help='Load all data types')
    parser.add_argument('--departures', action='store_true', help='Load departures')
    parser.add_argument('--stops', action='store_true', help='Load stops')
    parser.add_argument('--gtfs', action='store_true', help='Load GTFS')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be loaded')
    parser.add_argument('--create-tables', action='store_true', help='Create tables before loading')
    args = parser.parse_args()
    
    # Default to all if nothing specified
    if not any([args.departures, args.stops, args.gtfs]):
        args.all = True
    
    print("=" * 60)
    print("Transit System - Load Data to Snowflake")
    print("=" * 60)
    
    # Load secrets
    print("\n📁 Loading secrets...")
    secrets = load_secrets()
    print(f"  ✓ Database: {secrets['SNOWFLAKE_DATABASE']}")
    
    # Connect to Snowflake
    print("\n🔗 Connecting to Snowflake...")
    conn = get_snowflake_connection(secrets)
    print(f"  ✓ Connected to {secrets['SNOWFLAKE_ACCOUNT']}")
    
    # Create tables if requested
    if args.create_tables:
        create_tables_if_not_exist(conn)
    
    # Data directory
    data_dir = project_root / "ingestion" / "data" / "local_test"
    print(f"\n📂 Data directory: {data_dir}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No data will be loaded\n")
    
    total_loaded = 0
    
    # Load data types
    if args.all or args.departures:
        print("\n📤 Loading Departures...")
        total_loaded += load_departures(conn, data_dir, args.dry_run)
    
    if args.all or args.stops:
        print("\n📤 Loading Stops...")
        total_loaded += load_stops(conn, data_dir, args.dry_run)
    
    if args.all or args.gtfs:
        print("\n📤 Loading GTFS...")
        total_loaded += load_gtfs(conn, data_dir, args.dry_run)
    
    # Show counts
    if not args.dry_run:
        show_table_counts(conn)
    
    # Cleanup
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✓ Complete! Loaded {total_loaded} files")
    print("=" * 60)
    
    print("\n📋 Next steps:")
    print("  1. Run dbt models: cd dbt/transit_dbt && dbt run")
    print("  2. Query staging tables in Snowflake")
    print("  3. Start building dashboards!")


if __name__ == "__main__":
    main()

