"""
GTFS Incremental Data Fetcher
Fetches GTFS data incrementally starting from initial_load_date
First run: Loads data from Aug 1, 2025 onwards
Subsequent runs: Only fetches new data not already in database
OPTIMIZED: Uses bulk INSERT for fast loading
"""
import sys
from pathlib import Path
import os
import requests
import zipfile
import io
from datetime import datetime, timedelta
import json

# Calculate project root - works in both container and local
if os.path.exists('/opt/airflow'):
    project_root = Path('/opt/airflow')
else:
    project_root = Path(__file__).parent.parent

sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config
from api.warehouse_connection import get_warehouse_connection

def get_gtfs_feeds():
    """Get list of GTFS feeds to fetch"""
    return [
        {
            'agency': 'BART',
            'url': 'https://www.bart.gov/dev/schedules/google_transit.zip',
            'enabled': True
        },
        {
            'agency': 'VTA',
            'url': 'https://gtfs.vta.org/gtfs_vta.zip',
            'enabled': True
        }
    ]

def init_landing_tables():
    """Initialize landing tables for GTFS data in Snowflake"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        raise ValueError("Only Snowflake is supported")
    
    sf_config = config.get_snowflake_config()
    schema = sf_config.get('schema', 'ANALYTICS')
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        
        # GTFS Stops
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.LANDING_GTFS_STOPS (
                STOP_ID VARCHAR(255),
                STOP_CODE VARCHAR(100),
                STOP_NAME VARCHAR(500),
                STOP_DESC VARCHAR(1000),
                STOP_LAT FLOAT,
                STOP_LON FLOAT,
                ZONE_ID VARCHAR(100),
                STOP_URL VARCHAR(500),
                LOCATION_TYPE INTEGER,
                PARENT_STATION VARCHAR(255),
                AGENCY VARCHAR(100),
                FEED_ID VARCHAR(255),
                LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                PRIMARY KEY (STOP_ID, FEED_ID)
            )
        """)
        
        # GTFS Routes
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.LANDING_GTFS_ROUTES (
                ROUTE_ID VARCHAR(255),
                AGENCY_ID VARCHAR(100),
                ROUTE_SHORT_NAME VARCHAR(100),
                ROUTE_LONG_NAME VARCHAR(500),
                ROUTE_DESC VARCHAR(1000),
                ROUTE_TYPE INTEGER,
                ROUTE_URL VARCHAR(500),
                ROUTE_COLOR VARCHAR(10),
                ROUTE_TEXT_COLOR VARCHAR(10),
                AGENCY VARCHAR(100),
                FEED_ID VARCHAR(255),
                LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                PRIMARY KEY (ROUTE_ID, FEED_ID)
            )
        """)
        
        # GTFS Trips
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.LANDING_GTFS_TRIPS (
                TRIP_ID VARCHAR(255),
                ROUTE_ID VARCHAR(255),
                SERVICE_ID VARCHAR(255),
                TRIP_HEADSIGN VARCHAR(500),
                TRIP_SHORT_NAME VARCHAR(100),
                DIRECTION_ID INTEGER,
                BLOCK_ID VARCHAR(255),
                SHAPE_ID VARCHAR(255),
                WHEELCHAIR_ACCESSIBLE INTEGER,
                AGENCY VARCHAR(100),
                FEED_ID VARCHAR(255),
                LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                PRIMARY KEY (TRIP_ID, FEED_ID)
            )
        """)
        
        # GTFS Stop Times
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.LANDING_GTFS_STOP_TIMES (
                TRIP_ID VARCHAR(255),
                ARRIVAL_TIME VARCHAR(50),
                DEPARTURE_TIME VARCHAR(50),
                STOP_ID VARCHAR(255),
                STOP_SEQUENCE INTEGER,
                STOP_HEADSIGN VARCHAR(500),
                PICKUP_TYPE INTEGER,
                DROP_OFF_TYPE INTEGER,
                SHAPE_DIST_TRAVELED FLOAT,
                TIMEPOINT INTEGER,
                AGENCY VARCHAR(100),
                FEED_ID VARCHAR(255),
                SERVICE_DATE VARCHAR(50),
                LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                PRIMARY KEY (TRIP_ID, STOP_ID, STOP_SEQUENCE, FEED_ID, SERVICE_DATE)
            )
        """)
        
        # Streaming Departures Landing Table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.LANDING_STREAMING_DEPARTURES (
                ID VARCHAR(255),
                TIMESTAMP VARCHAR(100),
                GLOBAL_STOP_ID VARCHAR(255),
                STOP_NAME VARCHAR(500),
                GLOBAL_ROUTE_ID VARCHAR(255),
                ROUTE_SHORT_NAME VARCHAR(100),
                ROUTE_LONG_NAME VARCHAR(500),
                AGENCY VARCHAR(100),
                CITY VARCHAR(100),
                SCHEDULED_DEPARTURE_TIME BIGINT,
                DEPARTURE_TIME BIGINT,
                IS_REAL_TIME BOOLEAN,
                TRIP_SEARCH_KEY VARCHAR(255),
                DELAY_SECONDS INTEGER,
                CONSUMED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                PRIMARY KEY (ID)
            )
        """)
        
        # Load history
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.GTFS_LOAD_HISTORY (
                FEED_ID VARCHAR(255) PRIMARY KEY,
                AGENCY VARCHAR(100),
                LAST_LOAD_DATE VARCHAR(50),
                LAST_LOAD_TIMESTAMP TIMESTAMP_NTZ,
                RECORDS_LOADED INTEGER
            )
        """)
        
        conn.commit()
        print("✓ Landing tables initialized in Snowflake")

def download_gtfs_feed(url: str) -> bytes:
    """Download GTFS feed ZIP file"""
    print(f"  Downloading GTFS feed from {url}...")
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; TransitSystem/1.0)'}
    response = requests.get(url, timeout=120, headers=headers)
    response.raise_for_status()
    return response.content

def parse_gtfs_file(zip_content: bytes, filename: str) -> list:
    """Parse a GTFS CSV file from ZIP"""
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
        if filename not in zip_file.namelist():
            return []
        
        with zip_file.open(filename) as f:
            lines = f.read().decode('utf-8').split('\n')
            if not lines:
                return []
            
            import csv
            reader = csv.DictReader(lines)
            return list(reader)

def has_agency_data(agency: str) -> bool:
    """Check if we already have data for this agency (GTFS is static, not daily)"""
    config = get_warehouse_config()
    sf_config = config.get_snowflake_config()
    schema = sf_config.get('schema', 'ANALYTICS')
    
    try:
        with get_warehouse_connection() as conn:
            cursor = conn.cursor()
            # Check if we have any stops for this agency (quick check)
            cursor.execute(f"""
                SELECT COUNT(*) FROM {schema}.LANDING_GTFS_STOPS
                WHERE AGENCY = %s
            """, (agency,))
            count = cursor.fetchone()[0]
            return count > 0
    except Exception:
        return False

def get_last_load_date(feed_id: str) -> str:
    """Get last load date for a feed from Snowflake"""
    config = get_warehouse_config()
    sf_config = config.get_snowflake_config()
    schema = sf_config.get('schema', 'ANALYTICS')
    
    try:
        with get_warehouse_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT LAST_LOAD_DATE FROM {schema}.GTFS_LOAD_HISTORY
                WHERE FEED_ID = %s
            """, (feed_id,))
            
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        pass
    
    return config.get_initial_load_date()

def load_gtfs_feed(agency: str, url: str):
    """Load GTFS feed into Snowflake landing tables - OPTIMIZED with bulk inserts"""
    print(f"\n📥 Loading GTFS feed for {agency}...")
    
    # GTFS is static schedule data, not daily - check if we already have it
    if has_agency_data(agency):
        print(f"  ⏭️  Skipping: GTFS data for {agency} already exists (static schedule, not daily)")
        print(f"  💡 GTFS schedules don't change daily. Use streaming data for real-time updates.")
        return 0
    
    feed_id = f"{agency}_{datetime.now().strftime('%Y%m%d')}"
    last_load_date = get_last_load_date(feed_id)
    initial_load_date = get_warehouse_config().get_initial_load_date()
    
    if last_load_date and last_load_date >= initial_load_date:
        start_date = (datetime.strptime(last_load_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"  Initial load from {start_date}")
    else:
        start_date = initial_load_date
        print(f"  Initial load from {start_date}")
    
    # Download feed
    try:
        zip_content = download_gtfs_feed(url)
    except Exception as e:
        print(f"  ❌ Error downloading feed: {e}")
        return 0
    
    # Parse all files first (staging)
    print("  📦 Parsing GTFS files...")
    stops = parse_gtfs_file(zip_content, 'stops.txt')
    routes = parse_gtfs_file(zip_content, 'routes.txt')
    trips = parse_gtfs_file(zip_content, 'trips.txt')
    stop_times = parse_gtfs_file(zip_content, 'stop_times.txt')
    
    print(f"  ✓ Parsed: {len(stops)} stops, {len(routes)} routes, {len(trips)} trips, {len(stop_times)} stop_times")
    
    # Load data to Snowflake using bulk inserts
    config = get_warehouse_config()
    sf_config = config.get_snowflake_config()
    schema = sf_config.get('schema', 'ANALYTICS')
    
    records_loaded = 0
    service_date = datetime.now().strftime('%Y-%m-%d')
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        
        # Delete existing data for this feed (for clean reload)
        print("  🗑️  Clearing existing data for this feed...")
        cursor.execute(f"DELETE FROM {schema}.LANDING_GTFS_STOPS WHERE FEED_ID = %s", (feed_id,))
        cursor.execute(f"DELETE FROM {schema}.LANDING_GTFS_ROUTES WHERE FEED_ID = %s", (feed_id,))
        cursor.execute(f"DELETE FROM {schema}.LANDING_GTFS_TRIPS WHERE FEED_ID = %s", (feed_id,))
        cursor.execute(f"DELETE FROM {schema}.LANDING_GTFS_STOP_TIMES WHERE FEED_ID = %s", (feed_id,))
        
        # Bulk insert stops
        if stops:
            print(f"  ⚡ Bulk inserting {len(stops)} stops...")
            def clean_numeric(value, default=None):
                if value == '' or value is None:
                    return default
                try:
                    return int(value) if default is not None and isinstance(default, int) else float(value)
                except (ValueError, TypeError):
                    return default
            
            stop_values = [(
                stop.get('stop_id'),
                stop.get('stop_code'),
                stop.get('stop_name'),
                stop.get('stop_desc'),
                clean_numeric(stop.get('stop_lat'), None),
                clean_numeric(stop.get('stop_lon'), None),
                stop.get('zone_id'),
                stop.get('stop_url'),
                clean_numeric(stop.get('location_type'), 0),
                stop.get('parent_station'),
                agency,
                feed_id
            ) for stop in stops]
            
            cursor.executemany(f"""
                INSERT INTO {schema}.LANDING_GTFS_STOPS
                (STOP_ID, STOP_CODE, STOP_NAME, STOP_DESC, STOP_LAT, STOP_LON,
                 ZONE_ID, STOP_URL, LOCATION_TYPE, PARENT_STATION, AGENCY, FEED_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, stop_values)
            records_loaded += len(stops)
            print(f"  ✅ Loaded {len(stops)} stops")
        
        # Bulk insert routes
        if routes:
            print(f"  ⚡ Bulk inserting {len(routes)} routes...")
            def clean_numeric(value, default=None):
                if value == '' or value is None:
                    return default
                try:
                    return int(value) if default is not None and isinstance(default, int) else float(value)
                except (ValueError, TypeError):
                    return default
            
            route_values = [(
                route.get('route_id'),
                route.get('agency_id'),
                route.get('route_short_name'),
                route.get('route_long_name'),
                route.get('route_desc'),
                clean_numeric(route.get('route_type'), None),
                route.get('route_url'),
                route.get('route_color'),
                route.get('route_text_color'),
                agency,
                feed_id
            ) for route in routes]
            
            cursor.executemany(f"""
                INSERT INTO {schema}.LANDING_GTFS_ROUTES
                (ROUTE_ID, AGENCY_ID, ROUTE_SHORT_NAME, ROUTE_LONG_NAME, ROUTE_DESC,
                 ROUTE_TYPE, ROUTE_URL, ROUTE_COLOR, ROUTE_TEXT_COLOR, AGENCY, FEED_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, route_values)
            records_loaded += len(routes)
            print(f"  ✅ Loaded {len(routes)} routes")
        
        # Bulk insert trips
        if trips:
            print(f"  ⚡ Bulk inserting {len(trips)} trips...")
            def clean_numeric(value, default=None):
                if value == '' or value is None:
                    return default
                try:
                    return int(value) if default is not None and isinstance(default, int) else float(value)
                except (ValueError, TypeError):
                    return default
            
            trip_values = [(
                trip.get('trip_id'),
                trip.get('route_id'),
                trip.get('service_id'),
                trip.get('trip_headsign'),
                trip.get('trip_short_name'),
                clean_numeric(trip.get('direction_id'), None),
                trip.get('block_id'),
                trip.get('shape_id'),
                clean_numeric(trip.get('wheelchair_accessible'), None),
                agency,
                feed_id
            ) for trip in trips]
            
            cursor.executemany(f"""
                INSERT INTO {schema}.LANDING_GTFS_TRIPS
                (TRIP_ID, ROUTE_ID, SERVICE_ID, TRIP_HEADSIGN, TRIP_SHORT_NAME,
                 DIRECTION_ID, BLOCK_ID, SHAPE_ID, WHEELCHAIR_ACCESSIBLE, AGENCY, FEED_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, trip_values)
            records_loaded += len(trips)
            print(f"  ✅ Loaded {len(trips)} trips")
        
        # Bulk insert stop_times (in batches for very large files)
        if stop_times:
            batch_size = 10000
            total_batches = (len(stop_times) + batch_size - 1) // batch_size
            print(f"  ⚡ Bulk inserting {len(stop_times)} stop_times in {total_batches} batches...")
            
            def clean_numeric(value, default=None):
                """Convert empty string to None for numeric fields"""
                if value == '' or value is None:
                    return default
                try:
                    return int(value) if default is not None and isinstance(default, int) else float(value)
                except (ValueError, TypeError):
                    return default
            
            for i in range(0, len(stop_times), batch_size):
                batch = stop_times[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                
                stop_time_values = [(
                    stop_time.get('trip_id'),
                    stop_time.get('arrival_time'),
                    stop_time.get('departure_time'),
                    stop_time.get('stop_id'),
                    clean_numeric(stop_time.get('stop_sequence'), 0),
                    stop_time.get('stop_headsign'),
                    clean_numeric(stop_time.get('pickup_type'), 0),
                    clean_numeric(stop_time.get('drop_off_type'), 0),
                    clean_numeric(stop_time.get('shape_dist_traveled'), None),
                    clean_numeric(stop_time.get('timepoint'), 1),
                    agency,
                    feed_id,
                    service_date
                ) for stop_time in batch]
                
                cursor.executemany(f"""
                    INSERT INTO {schema}.LANDING_GTFS_STOP_TIMES
                    (TRIP_ID, ARRIVAL_TIME, DEPARTURE_TIME, STOP_ID, STOP_SEQUENCE,
                     STOP_HEADSIGN, PICKUP_TYPE, DROP_OFF_TYPE, SHAPE_DIST_TRAVELED,
                     TIMEPOINT, AGENCY, FEED_ID, SERVICE_DATE)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, stop_time_values)
                
                if batch_num % 10 == 0 or batch_num == total_batches:
                    print(f"    Batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            records_loaded += len(stop_times)
            print(f"  ✅ Loaded {len(stop_times)} stop_times")
        
        # Update load history
        cursor.execute(f"""
            MERGE INTO {schema}.GTFS_LOAD_HISTORY AS target
            USING (SELECT %s AS FEED_ID) AS source
            ON target.FEED_ID = source.FEED_ID
            WHEN MATCHED THEN
                UPDATE SET
                    AGENCY = %s, LAST_LOAD_DATE = %s, LAST_LOAD_TIMESTAMP = CURRENT_TIMESTAMP(),
                    RECORDS_LOADED = %s
            WHEN NOT MATCHED THEN
                INSERT (FEED_ID, AGENCY, LAST_LOAD_DATE, LAST_LOAD_TIMESTAMP, RECORDS_LOADED)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP(), %s)
        """, (
            feed_id,
            agency, datetime.now().strftime('%Y-%m-%d'), records_loaded,
            feed_id, agency, datetime.now().strftime('%Y-%m-%d'), records_loaded
        ))
        
        conn.commit()
    
    print(f"  ✅ Total records loaded: {records_loaded:,}")
    return records_loaded

def main():
    """Main function"""
    import time
    start_time = time.time()
    
    config = get_warehouse_config()
    
    print("=" * 70)
    print("🚂 GTFS Incremental Data Loader (OPTIMIZED)")
    print("=" * 70)
    print(f"Initial load date: {config.get_initial_load_date()}")
    print(f"Incremental: {config.is_incremental_enabled()}")
    print(f"Warehouse: {config.warehouse_type}")
    print()
    
    init_landing_tables()
    
    feeds = get_gtfs_feeds()
    total_records = 0
    
    for feed in feeds:
        if not feed.get('enabled', True):
            continue
        
        try:
            records = load_gtfs_feed(feed['agency'], feed['url'])
            total_records += records
        except Exception as e:
            print(f"  ❌ Error loading {feed['agency']}: {e}")
            import traceback
            traceback.print_exc()
    
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"✅ Total records loaded: {total_records:,}")
    print(f"⏱️  Time taken: {elapsed:.1f} seconds")
    print(f"📊 Speed: {total_records/elapsed:.0f} records/second")
    print("=" * 70)

if __name__ == "__main__":
    main()
