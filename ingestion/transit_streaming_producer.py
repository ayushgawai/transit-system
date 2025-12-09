#!/usr/bin/env python3
"""
Transit API Streaming Producer
Fetches data from Transit API for ALL stops in multiple cities and writes directly to Snowflake
Based on user's working script, updated to fetch data for all stops
"""
import sys
from pathlib import Path
import os
import time
import json
import hashlib
from datetime import datetime
import requests
import snowflake.connector

# Calculate project root
if os.path.exists('/opt/airflow'):
    project_root = Path('/opt/airflow')
else:
    project_root = Path(__file__).parent.parent

sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config

BASE = "https://external.transitapp.com/v3"

def get_transit_api_key():
    """Get Transit API key from config"""
    config = get_warehouse_config()
    api_key = config.get_transit_api_key()
    if not api_key:
        raise ValueError("Transit API key not found. Please configure it in AWS Secrets Manager or set TRANSIT_API_KEY environment variable.")
    return api_key

def get_snowflake_connection():
    """Get Snowflake connection"""
    config = get_warehouse_config()
    snowflake_config = config.get_snowflake_config()
    
    return snowflake.connector.connect(
        user=snowflake_config.get('user'),
        password=snowflake_config.get('password'),
        account=snowflake_config.get('account'),
        warehouse=snowflake_config.get('warehouse'),
        database=snowflake_config.get('database'),
        schema='ANALYTICS'
    )

def init_streaming_table(conn):
    """Initialize streaming table if it doesn't exist"""
    cursor = conn.cursor()
    config = get_warehouse_config()
    snowflake_config = config.get_snowflake_config()
    database = snowflake_config.get('database', 'USER_DB_HORNET')
    
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {database}.LANDING.LANDING_STREAMING_DEPARTURES (
        ID VARCHAR(255) PRIMARY KEY,
        TIMESTAMP VARCHAR(50),
        GLOBAL_STOP_ID VARCHAR(255),
        STOP_NAME VARCHAR(500),
        GLOBAL_ROUTE_ID VARCHAR(255),
        ROUTE_SHORT_NAME VARCHAR(255),
        ROUTE_LONG_NAME VARCHAR(500),
        AGENCY VARCHAR(100),
        CITY VARCHAR(100),
        SCHEDULED_DEPARTURE_TIME BIGINT,
        DEPARTURE_TIME BIGINT,
        IS_REAL_TIME BOOLEAN,
        TRIP_SEARCH_KEY VARCHAR(500),
        DELAY_SECONDS INTEGER,
        CONSUMED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ Streaming table ready")
    except Exception as e:
        print(f"⚠️  Table creation check: {e}")

def api_get(path, params, api_key):
    """Make API request"""
    headers = {"apiKey": api_key, "Accept-Language": "en"}
    r = requests.get(f"{BASE}/{path}", headers=headers, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def nearest_stop(lat, lon, max_distance=600, api_key=None):
    """Get nearest stop"""
    data = api_get("public/nearby_stops", {"lat": lat, "lon": lon, "max_distance": max_distance}, api_key)
    stops = data.get("stops", [])
    if not stops:
        return None
    return stops[0]  # choose the closest

def fmt_iso(ts=None):
    """Format ISO timestamp"""
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def fetch_all_stops_for_locations(api_key, locations):
    """Fetch all nearby stops for multiple locations"""
    all_stops = []
    seen_stop_ids = set()
    
    for city_name, lat, lon in locations:
        print(f"📍 Fetching stops for {city_name} ({lat}, {lon})...")
        try:
            data = api_get("public/nearby_stops", {
                "lat": lat,
                "lon": lon,
                "max_distance": 2000  # 2km radius
            }, api_key)
            
            stops = data.get("stops", [])
            new_count = 0
            for stop in stops:
                stop_id = stop.get("global_stop_id")
                if stop_id and stop_id not in seen_stop_ids:
                    seen_stop_ids.add(stop_id)
                    # Add city info to stop
                    stop["city"] = city_name
                    all_stops.append(stop)
                    new_count += 1
            
            print(f"  ✅ Found {len(stops)} stops ({new_count} new)")
        except Exception as e:
            print(f"  ⚠️  Error fetching stops for {city_name}: {e}")
    
    return all_stops

def insert_to_snowflake(conn, events):
    """Bulk insert events to Snowflake"""
    if not events:
        return 0
    
    cursor = conn.cursor()
    config = get_warehouse_config()
    snowflake_config = config.get_snowflake_config()
    database = snowflake_config.get('database', 'USER_DB_HORNET')
    
    insert_sql = f"""
    INSERT INTO {database}.LANDING.LANDING_STREAMING_DEPARTURES 
    (ID, TIMESTAMP, GLOBAL_STOP_ID, STOP_NAME, GLOBAL_ROUTE_ID, ROUTE_SHORT_NAME, 
     ROUTE_LONG_NAME, AGENCY, CITY, SCHEDULED_DEPARTURE_TIME, DEPARTURE_TIME, 
     IS_REAL_TIME, TRIP_SEARCH_KEY, DELAY_SECONDS, CONSUMED_AT)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
    """
    
    rows = []
    for event in events:
        # Generate unique ID
        key = f"{event.get('stop_id')}_{event.get('route_id')}_{event.get('scheduled_epoch')}"
        event_id = hashlib.md5(key.encode()).hexdigest()
        
        rows.append((
            event_id,
            event.get('ts'),
            event.get('stop_id'),
            event.get('stop_name'),
            event.get('route_id'),
            event.get('route'),  # route_short_name
            event.get('route_long') or event.get('route'),  # route_long_name
            event.get('agency', 'Unknown'),
            event.get('city', 'Unknown'),
            event.get('scheduled_epoch'),
            event.get('predicted_epoch'),
            event.get('is_real_time', False),
            event.get('trip_key', ''),
            event.get('delay_seconds')
        ))
    
    try:
        cursor.executemany(insert_sql, rows)
        conn.commit()
        print(f"  ✅ Inserted {len(rows)} records to Snowflake")
        return len(rows)
    except Exception as e:
        print(f"  ⚠️  Error inserting: {e}")
        conn.rollback()
        return 0

def main():
    """Main streaming loop - fetches data for all stops in multiple cities"""
    api_key = get_transit_api_key()
    if not api_key:
        print("❌ Transit API key not found")
        return
    
    # Connect to Snowflake
    try:
        conn = get_snowflake_connection()
        init_streaming_table(conn)
        print("✅ Connected to Snowflake")
    except Exception as e:
        print(f"❌ Failed to connect to Snowflake: {e}")
        return
    
    # Multiple locations to cover San Jose, San Francisco, and surrounding areas
    locations = [
        ("San Jose", 37.3382, -121.8863),
        ("San Francisco", 37.7749, -122.4194),
        ("Mountain View", 37.3861, -122.0839),
        ("Palo Alto", 37.4419, -122.1430),
        ("Sunnyvale", 37.3688, -122.0363),
    ]
    
    print("=" * 70)
    print("🔍 DISCOVERING ALL STOPS")
    print("=" * 70)
    
    # Fetch all stops once at startup
    all_stops = fetch_all_stops_for_locations(api_key, locations)
    
    if not all_stops:
        print("❌ No stops found")
        return
    
    print(f"\n✅ Total unique stops discovered: {len(all_stops)}")
    
    # Group by agency for reporting
    agencies = {}
    for stop in all_stops:
        stop_id = stop.get("global_stop_id", "")
        agency = stop_id.split(":")[0] if ":" in stop_id else "Unknown"
        agencies[agency] = agencies.get(agency, 0) + 1
    
    print("\nStops by agency:")
    for agency, count in sorted(agencies.items()):
        print(f"  {agency}: {count} stops")
    
    cycle_time_min = len(all_stops) * 12 / 60  # 12 seconds per stop
    print(f"\n⏱️  Streaming cycle: {len(all_stops)} stops, ~{cycle_time_min:.1f} minutes per full cycle")
    print(f"   (Rate limit: 5 calls per minute = 12 seconds between calls)")
    print()
    
    seen = {}  # key -> last departure_time signature
    total_inserted = 0
    
    try:
        while True:
            cycle_start = time.time()
            cycle_inserted = 0
            
            print(f"🔄 Starting new cycle ({len(all_stops)} stops)...")
            
            # Cycle through all stops
            for i, stop in enumerate(all_stops):
                stop_id = stop.get("global_stop_id")
                stop_name = stop.get("stop_name", stop_id)
                city = stop.get("city", "Unknown")
                
                try:
                    # Fetch departures for this stop
                    data = api_get("public/stop_departures", {
                        "global_stop_id": stop_id,
                        "max_num_departures": 10,
                        "should_update_realtime": "true"
                    }, api_key)
                    
                    events = []
                    
                    for rd in data.get("route_departures", []):
                        route_id = rd.get("global_route_id")
                        route_short = rd.get("route_short_name") or route_id
                        route_long = rd.get("route_long_name") or route_short
                        
                        # Infer agency from stop_id prefix first (most reliable), then route_id
                        agency = 'Unknown'
                        if stop_id and ":" in stop_id:
                            stop_prefix = stop_id.split(":")[0].upper()
                            if stop_prefix == 'BART':
                                agency = 'BART'
                            elif stop_prefix == 'VTA':
                                agency = 'VTA'
                            elif stop_prefix == 'MUNI':
                                agency = 'MUNI'
                            elif stop_prefix in ['CALT', 'CALTRAIN']:
                                agency = 'Caltrain'
                            else:
                                agency = stop_prefix  # Use prefix as agency name
                        elif route_id:
                            route_upper = route_id.upper()
                            if 'BART' in route_upper:
                                agency = 'BART'
                            elif 'VTA' in route_upper:
                                agency = 'VTA'
                            elif 'MUNI' in route_upper:
                                agency = 'MUNI'
                        
                        for it in rd.get("itineraries", []):
                            headsign = it.get("merged_headsign") or it.get("headsign") or ""
                            direction_id = it.get("direction_id")
                            
                            for item in it.get("schedule_items", []):
                                # Create stable key for change detection
                                key = (
                                    item.get("trip_search_key")
                                    or item.get("rt_trip_id")
                                    or f"{stop_id}|{route_id}|{direction_id}|{item.get('scheduled_departure_time')}"
                                )
                                
                                signature = item.get("departure_time")
                                if seen.get(key) == signature:
                                    continue  # Skip duplicates
                                seen[key] = signature
                                
                                # Build event
                                sched = item.get("scheduled_departure_time")
                                actual = item.get("departure_time")
                                is_rt = bool(item.get("is_real_time"))
                                delay = None
                                if is_rt and sched and actual:
                                    delay = int(actual - sched)  # seconds
                                
                                events.append({
                                    "ts": fmt_iso(),
                                    "stop_id": stop_id,
                                    "stop_name": stop_name,
                                    "route_id": route_id,
                                    "route": route_short,
                                    "route_long": route_long,
                                    "headsign": headsign,
                                    "is_real_time": is_rt,
                                    "scheduled_epoch": sched,
                                    "predicted_epoch": actual,
                                    "delay_seconds": delay,
                                    "trip_key": key,
                                    "agency": agency,
                                    "city": city
                                })
                    
                    if events:
                        inserted = insert_to_snowflake(conn, events)
                        cycle_inserted += inserted
                        total_inserted += inserted
                        if (i + 1) % 50 == 0:  # Print progress every 50 stops
                            print(f"  📊 Progress: {i+1}/{len(all_stops)} stops, {cycle_inserted} records this cycle")
                
                except Exception as e:
                    print(f"  ⚠️  Error fetching {stop_name}: {e}")
                    # Continue with next stop
                
                # Rate limit: 5 calls per minute = 12 seconds between calls
                if i < len(all_stops) - 1:  # Don't sleep after last stop
                    time.sleep(12)  # 12 seconds between calls
            
            cycle_time = time.time() - cycle_start
            print(f"\n✅ Cycle complete: {cycle_inserted} new records, {cycle_time/60:.1f} minutes")
            print(f"📊 Total records inserted: {total_inserted}")
            print(f"⏱️  Next cycle starting in 60 seconds...\n")
            time.sleep(60)  # Wait 1 minute before next cycle
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        conn.close()
        print(f"\n✅ Streaming complete. Total records inserted: {total_inserted}")

if __name__ == "__main__":
    main()
