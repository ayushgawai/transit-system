"""
Streaming Data Fetcher for TransitApp API
Fetches real-time data and stores in streaming table, then merges to main tables
Based on TransitApp API v3 documentation: https://api-doc.transitapp.com/v3.html
"""
import os
import sys
from pathlib import Path
import sqlite3
import yaml
import requests
from datetime import datetime
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_api_key():
    """Get TransitApp API key from secrets.yaml or environment"""
    secrets_path = project_root / "secrets.yaml"
    if secrets_path.exists():
        with open(secrets_path) as f:
            secrets = yaml.safe_load(f)
        api_key = secrets.get('TRANSIT_APP_API_KEY', '')
        if api_key and not api_key.startswith('your_'):
            return api_key
    # Try environment variable
    api_key = os.environ.get('TRANSIT_API_KEY') or os.environ.get('TRANSIT_APP_API_KEY')
    if api_key:
        return api_key
    raise ValueError("TransitApp API key not found. Please set TRANSIT_API_KEY or TRANSIT_APP_API_KEY environment variable, or configure in secrets.yaml")

def call_transitapp_api(api_key: str, endpoint: str, params: dict = None):
    """Call TransitApp API"""
    base_url = "https://external.transitapp.com/v3"
    url = f"{base_url}/{endpoint}"
    headers = {
        "apiKey": api_key,
        "Accept-Language": "en",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:200]}")
        return None

def fetch_nearby_stops(api_key: str, lat: float, lon: float, max_distance: int = 1000):
    """Fetch nearby stops"""
    params = {
        "lat": lat,
        "lon": lon,
        "max_distance": max_distance
    }
    response = call_transitapp_api(api_key, "public/nearby_stops", params)
    return response.get("stops", []) if response else []

def fetch_stop_departures(api_key: str, global_stop_id: str, max_num_departures: int = 8):
    """Fetch real-time departures for a stop"""
    params = {
        "global_stop_id": global_stop_id,
        "max_num_departures": max_num_departures,
        "should_update_realtime": "true"
    }
    response = call_transitapp_api(api_key, "public/stop_departures", params)
    return response if response else {}

def init_streaming_table(db_path: Path):
    """Initialize streaming table"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create streaming_departures table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streaming_departures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            global_stop_id TEXT NOT NULL,
            stop_name TEXT,
            route_id TEXT,
            route_name TEXT,
            agency TEXT,
            scheduled_time TEXT,
            predicted_time TEXT,
            delay_seconds INTEGER,
            is_realtime BOOLEAN DEFAULT 1,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            city TEXT,
            trip_search_key TEXT,
            UNIQUE(global_stop_id, route_id, trip_search_key, fetched_at)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_streaming_agency ON streaming_departures(agency)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_streaming_fetched ON streaming_departures(fetched_at)
    """)
    
    conn.commit()
    conn.close()
    print("✓ Streaming table initialized")

def save_streaming_data(db_path: Path, departures_data: list):
    """Save streaming data to streaming_departures table"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    inserted = 0
    
    for dep_data in departures_data:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO streaming_departures 
                (global_stop_id, stop_name, route_id, route_name, agency, 
                 scheduled_time, predicted_time, delay_seconds, is_realtime, fetched_at, city, trip_search_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dep_data.get('global_stop_id'),
                dep_data.get('stop_name'),
                dep_data.get('route_id'),
                dep_data.get('route_name'),
                dep_data.get('agency'),
                dep_data.get('scheduled_time'),
                dep_data.get('predicted_time'),
                dep_data.get('delay_seconds'),
                dep_data.get('is_realtime', True),
                now,
                dep_data.get('city'),
                dep_data.get('trip_search_key')
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting: {e}")
            print(f"  Data: {dep_data}")
    
    conn.commit()
    conn.close()
    print(f"✓ Saved {inserted} new streaming departures")
    return inserted

def merge_to_main_tables(db_path: Path):
    """Merge streaming data to main departures table"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Merge streaming data to main departures table
    # Note: departures table uses actual_departure_time (not predicted_departure_time)
    # and scheduled_departure_time is INTEGER (epoch), not TEXT
    cursor.execute("""
        INSERT OR REPLACE INTO departures 
        (departure_id, stop_id, route_id, global_route_id,
         agency, scheduled_departure_time, actual_departure_time, delay_seconds, 
         is_real_time, load_timestamp, city)
        SELECT 
            'STREAM_' || s.id,
            s.global_stop_id,
            s.route_id,
            s.route_id,
            s.agency,
            CAST(strftime('%s', s.scheduled_time) AS INTEGER),
            CAST(strftime('%s', s.predicted_time) AS INTEGER),
            s.delay_seconds,
            CASE WHEN s.is_realtime THEN 1 ELSE 0 END,
            s.fetched_at,
            s.city
        FROM streaming_departures s
        WHERE s.fetched_at >= datetime('now', '-1 hour')
        AND s.scheduled_time IS NOT NULL
        AND s.predicted_time IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM departures d 
            WHERE d.departure_id = 'STREAM_' || s.id
        )
    """)
    
    merged = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"✓ Merged {merged} records to main departures table")
    return merged

def fetch_and_save_streaming_data():
    """Main function to fetch and save streaming data"""
    api_key = get_api_key()
    if not api_key:
        print("✗ API key not configured")
        return
    
    db_path = project_root / "data" / "local_transit.db"
    init_streaming_table(db_path)
    
    # Monitoring locations (SF Bay Area)
    locations = [
        (37.7749, -122.4194, "San Francisco"),  # SF downtown (BART)
        (37.3382, -121.8863, "San Jose"),  # San Jose downtown (VTA)
    ]
    
    all_departures = []
    
    for lat, lon, city in locations:
        print(f"\n📍 Fetching stops near {city} ({lat}, {lon})...")
        stops = fetch_nearby_stops(api_key, lat, lon, max_distance=1500)
        print(f"  Found {len(stops)} stops")
        
        if not stops:
            print("  ⚠ No stops found, skipping location")
            continue
        
        # Limit to first 2 stops to respect rate limits
        for i, stop in enumerate(stops[:2]):
            stop_id = stop.get('global_stop_id')
            stop_name = stop.get('stop_name', stop.get('name', 'Unknown'))
            
            if not stop_id:
                print(f"  ⚠ Stop {i+1} has no global_stop_id, skipping")
                continue
                
            print(f"  [{i+1}/2] Fetching departures for {stop_name} ({stop_id})...")
            
            try:
                deps_data = fetch_stop_departures(api_key, stop_id, max_num_departures=8)
                
                if not deps_data:
                    print(f"    ⚠ No data returned")
                    continue
                
                # Parse the correct API structure based on TransitApp API v3 docs
                # Structure: route_departures -> route -> itineraries -> schedule_items
                route_departures = deps_data.get('route_departures', [])
                print(f"    Found {len(route_departures)} routes")
                
                for route_dep in route_departures:
                    # Get route info
                    route = route_dep.get('route', {})
                    global_route_id = route_dep.get('global_route_id') or route.get('global_route_id')
                    route_short_name = route_dep.get('route_short_name') or route.get('route_short_name') or global_route_id
                    route_long_name = route_dep.get('route_long_name') or route.get('route_long_name') or route_short_name
                    
                    # Get agency from route, stop, or infer from route_id/stop_id
                    agency = 'Unknown'
                    if route.get('agency'):
                        agency = route['agency'].get('name', 'Unknown') if isinstance(route['agency'], dict) else str(route['agency'])
                    elif stop.get('agency'):
                        agency = stop['agency'].get('name', 'Unknown') if isinstance(stop['agency'], dict) else str(stop['agency'])
                    
                    # Infer agency from route_id or stop_id if still unknown
                    if agency == 'Unknown':
                        if global_route_id:
                            if global_route_id.startswith('BART:'):
                                agency = 'BART'
                            elif global_route_id.startswith('VTA:'):
                                agency = 'VTA'
                            elif global_route_id.startswith('MUNI:'):
                                agency = 'MUNI'
                        if agency == 'Unknown' and stop_id:
                            if stop_id.startswith('BART:'):
                                agency = 'BART'
                            elif stop_id.startswith('VTA:'):
                                agency = 'VTA'
                            elif stop_id.startswith('MUNI:'):
                                agency = 'MUNI'
                    
                    # Process itineraries (directions)
                    itineraries = route_dep.get('itineraries', [])
                    for itinerary in itineraries:
                        # Process schedule_items (departures)
                        schedule_items = itinerary.get('schedule_items', [])
                        print(f"      Route {route_short_name}: {len(schedule_items)} departures")
                        
                        for item in schedule_items:
                            # Get timestamps (epoch seconds)
                            scheduled_epoch = item.get('scheduled_departure_time')
                            predicted_epoch = item.get('departure_time')
                            is_real_time = bool(item.get('is_real_time', False))
                            trip_search_key = item.get('trip_search_key')
                            
                            # Convert epoch to ISO format
                            scheduled_time = None
                            predicted_time = None
                            if scheduled_epoch:
                                scheduled_time = datetime.fromtimestamp(scheduled_epoch).isoformat()
                            if predicted_epoch:
                                predicted_time = datetime.fromtimestamp(predicted_epoch).isoformat()
                            
                            # Calculate delay
                            delay_seconds = None
                            if is_real_time and scheduled_epoch and predicted_epoch:
                                delay_seconds = int(predicted_epoch - scheduled_epoch)
                            
                            all_departures.append({
                                'global_stop_id': stop_id,
                                'stop_name': stop_name,
                                'route_id': global_route_id or route_short_name,
                                'route_name': route_long_name,
                                'agency': agency,
                                'scheduled_time': scheduled_time,
                                'predicted_time': predicted_time,
                                'delay_seconds': delay_seconds,
                                'is_realtime': is_real_time,
                                'city': city,
                                'trip_search_key': trip_search_key
                            })
                            
            except Exception as e:
                print(f"    ⚠ Error fetching departures: {e}")
                import traceback
                traceback.print_exc()
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print("    ⚠ Rate limit hit, stopping...")
                    break
            
            time.sleep(2)  # Rate limiting - wait 2 seconds between stops
    
    if all_departures:
        saved = save_streaming_data(db_path, all_departures)
        merge_to_main_tables(db_path)
        print(f"\n✅ Successfully fetched and saved {saved} streaming departures (out of {len(all_departures)} total)")
        return saved
    else:
        print("\n⚠ No departures fetched")
        return 0

if __name__ == "__main__":
    fetch_and_save_streaming_data()
