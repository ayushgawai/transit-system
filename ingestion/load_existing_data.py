"""
Load existing TransitApp JSON data into local SQLite database
This processes the real data we already have and loads it into a database
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Database path
DB_PATH = project_root / "data" / "local_transit.db"


def init_database():
    """Initialize SQLite database with tables"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create stops table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stops (
            stop_id TEXT PRIMARY KEY,
            global_stop_id TEXT UNIQUE,
            stop_name TEXT,
            stop_lat REAL,
            stop_lon REAL,
            route_type INTEGER,
            agency TEXT,
            stop_code TEXT,
            wheelchair_boarding INTEGER,
            parent_station_id TEXT,
            city TEXT,
            load_timestamp TEXT
        )
    """)
    
    # Create routes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            route_id TEXT PRIMARY KEY,
            global_route_id TEXT UNIQUE,
            route_name TEXT,
            route_short_name TEXT,
            route_long_name TEXT,
            route_type INTEGER,
            agency TEXT,
            route_color TEXT,
            city TEXT,
            load_timestamp TEXT
        )
    """)
    
    # Create departures table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departures (
            departure_id TEXT PRIMARY KEY,
            stop_id TEXT,
            route_id TEXT,
            global_route_id TEXT,
            trip_id TEXT,
            scheduled_departure_time INTEGER,
            scheduled_arrival_time INTEGER,
            actual_departure_time INTEGER,
            actual_arrival_time INTEGER,
            is_real_time INTEGER,
            is_cancelled INTEGER,
            delay_seconds INTEGER,
            direction_id INTEGER,
            direction_headsign TEXT,
            agency TEXT,
            city TEXT,
            load_timestamp TEXT,
            FOREIGN KEY (stop_id) REFERENCES stops(stop_id),
            FOREIGN KEY (route_id) REFERENCES routes(route_id)
        )
    """)
    
    # Create alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            route_id TEXT,
            global_route_id TEXT,
            title TEXT,
            description TEXT,
            severity TEXT,
            effect TEXT,
            created_at INTEGER,
            agency TEXT,
            load_timestamp TEXT
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_departures_stop ON departures(stop_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_departures_route ON departures(route_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_departures_time ON departures(scheduled_departure_time)")
    # Note: scheduled_departure_time column exists in the table definition above
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stops_agency ON stops(agency)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_agency ON routes(agency)")
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")


def extract_agency_from_id(global_id: str) -> str:
    """Extract agency name from global ID (format: AGENCY:ID)"""
    if ":" in global_id:
        return global_id.split(":")[0]
    return "UNKNOWN"


def map_route_type_to_name(route_type: int) -> str:
    """Map route type code to name"""
    route_type_map = {
        0: "Tram/Light Rail",
        1: "Subway",
        2: "Rail",
        3: "Bus",
        4: "Ferry",
        5: "Cable Car",
        6: "Gondola",
        7: "Funicular"
    }
    return route_type_map.get(route_type, f"Type {route_type}")


def load_stops_from_json(json_file: Path) -> int:
    """Load stops from JSON file"""
    with open(json_file) as f:
        data = json.load(f)
    
    stops = data.get("stops", [])
    if not stops:
        return 0
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    load_timestamp = datetime.utcnow().isoformat()
    
    loaded = 0
    for stop in stops:
        global_stop_id = stop.get("global_stop_id", "")
        if not global_stop_id:
            continue
        
        agency = extract_agency_from_id(global_stop_id)
        
        # Determine city based on agency
        city = "San Francisco Bay Area"
        if agency == "VTA":
            city = "San Jose"
        elif agency in ["BART", "MUNI", "SFMTA"]:
            city = "San Francisco Bay Area"
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO stops (
                    stop_id, global_stop_id, stop_name, stop_lat, stop_lon,
                    route_type, agency, stop_code, wheelchair_boarding,
                    parent_station_id, city, load_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                global_stop_id,  # Use global_stop_id as primary key
                global_stop_id,
                stop.get("stop_name", ""),
                stop.get("stop_lat"),
                stop.get("stop_lon"),
                stop.get("route_type", -1),
                agency,
                stop.get("stop_code", ""),
                stop.get("wheelchair_boarding", 0),
                stop.get("parent_station_global_stop_id"),
                city,
                load_timestamp
            ))
            loaded += 1
        except Exception as e:
            print(f"  ⚠️  Error loading stop {global_stop_id}: {e}")
            continue
    
    conn.commit()
    conn.close()
    return loaded


def load_departures_from_json(json_file: Path) -> int:
    """Load departures from JSON file"""
    with open(json_file) as f:
        data = json.load(f)
    
    # Handle different JSON structures
    # Structure 1: {"stop": {...}, "departures": {...}} - single stop
    if "stop" in data and "departures" in data:
        departures_dict = {"single_stop": data}
    # Structure 2: {"departures": {"stop_id": {"stop": {...}, "departures": {...}}}}
    elif "departures" in data and isinstance(data["departures"], dict):
        departures_dict = data["departures"]
    # Structure 3: {"departures": [{"stop": {...}, "departures": {...}}]}
    elif "departures" in data and isinstance(data["departures"], list):
        departures_dict = {f"stop_{i}": dep for i, dep in enumerate(data["departures"])}
    else:
        # Try direct structure - might be a list of stops
        if isinstance(data, list):
            departures_dict = {f"stop_{i}": item for i, item in enumerate(data)}
        else:
            departures_dict = {"unknown": data}
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    load_timestamp = datetime.utcnow().isoformat()
    
    loaded = 0
    
    for stop_key, stop_data in departures_dict.items():
        if isinstance(stop_data, dict):
            stop_info = stop_data.get("stop", {})
            departures_info = stop_data.get("departures", {})
        else:
            continue
        
        global_stop_id = stop_info.get("global_stop_id", "")
        if not global_stop_id:
            continue
        
        # Handle structure: {"departures": {"route_departures": [...]}}
        if "route_departures" in departures_info:
            route_departures = departures_info.get("route_departures", [])
        elif isinstance(departures_info, list):
            route_departures = departures_info
        else:
            route_departures = []
        
        for route_dep in route_departures:
            global_route_id = route_dep.get("global_route_id", "")
            agency = extract_agency_from_id(global_route_id) if global_route_id else extract_agency_from_id(global_stop_id)
            
            # Extract route name
            route_name = ""
            compact_display = route_dep.get("compact_display_short_name", {})
            if compact_display:
                elements = compact_display.get("elements", [])
                route_name = " ".join(str(e) for e in elements if e)
            
            # Save route
            if global_route_id:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO routes (
                            route_id, global_route_id, route_name, route_short_name,
                            route_long_name, agency, city, load_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        global_route_id,
                        global_route_id,
                        route_name or global_route_id,
                        route_name or global_route_id,
                        route_name or global_route_id,
                        agency,
                        "San Francisco Bay Area" if agency in ["BART", "MUNI"] else "San Jose" if agency == "VTA" else "Unknown",
                        load_timestamp
                    ))
                except Exception as e:
                    pass  # Route might already exist
            
            # Process itineraries
            itineraries = route_dep.get("itineraries", [])
            for itin in itineraries:
                schedule_items = itin.get("schedule_items", [])
                direction_headsign = itin.get("direction_headsign", "")
                direction_id = itin.get("direction_id", -1)
                
                for item in schedule_items:
                    trip_id = item.get("rt_trip_id", item.get("trip_search_key", ""))
                    scheduled_dep = item.get("scheduled_departure_time")
                    scheduled_arr = item.get("scheduled_arrival_time")
                    actual_dep = item.get("departure_time")
                    actual_arr = item.get("arrival_time")
                    
                    # Calculate delay
                    delay_seconds = None
                    if actual_dep and scheduled_dep:
                        delay_seconds = actual_dep - scheduled_dep
                    
                    departure_id = f"{global_stop_id}_{global_route_id}_{trip_id}_{scheduled_dep}"
                    
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO departures (
                                departure_id, stop_id, route_id, global_route_id,
                                trip_id, scheduled_departure_time, scheduled_arrival_time,
                                actual_departure_time, actual_arrival_time,
                                is_real_time, is_cancelled, delay_seconds,
                                direction_id, direction_headsign, agency, city, load_timestamp
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            departure_id,
                            global_stop_id,
                            global_route_id,
                            global_route_id,
                            trip_id,
                            scheduled_dep,
                            scheduled_arr,
                            actual_dep,
                            actual_arr,
                            1 if item.get("is_real_time", False) else 0,
                            1 if item.get("is_cancelled", False) else 0,
                            delay_seconds,
                            direction_id,
                            direction_headsign,
                            agency,
                            "San Francisco Bay Area" if agency in ["BART", "MUNI"] else "San Jose" if agency == "VTA" else "Unknown",
                            load_timestamp
                        ))
                        loaded += 1
                    except Exception as e:
                        print(f"  ⚠️  Error loading departure {departure_id}: {e}")
                        continue
    
    conn.commit()
    conn.close()
    return loaded


def main():
    """Main function to load existing data"""
    print("="*60)
    print("Loading Existing Transit Data into Local Database")
    print("="*60)
    
    # Initialize database
    init_database()
    
    # Find all JSON files
    data_dir = project_root / "ingestion" / "data" / "local_test" / "transitapp"
    
    stops_files = list(data_dir.rglob("stops_*.json"))
    departures_files = list(data_dir.rglob("departures_*.json"))
    
    print(f"\nFound {len(stops_files)} stops files and {len(departures_files)} departures files")
    
    # Load stops
    total_stops = 0
    print(f"\n{'='*60}")
    print("Loading Stops...")
    print(f"{'='*60}")
    for stops_file in stops_files:
        print(f"Loading {stops_file.name}...", end=" ")
        count = load_stops_from_json(stops_file)
        total_stops += count
        print(f"✓ {count} stops")
    
    # Load departures
    total_departures = 0
    print(f"\n{'='*60}")
    print("Loading Departures...")
    print(f"{'='*60}")
    for deps_file in departures_files:
        print(f"Loading {deps_file.name}...", end=" ")
        count = load_departures_from_json(deps_file)
        total_departures += count
        print(f"✓ {count} departures")
    
    # Summary
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM stops")
    stops_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM routes")
    routes_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM departures")
    deps_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT agency FROM stops")
    agencies = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    print(f"\n{'='*60}")
    print("LOAD SUMMARY")
    print(f"{'='*60}")
    print(f"Total stops in DB: {stops_count}")
    print(f"Total routes in DB: {routes_count}")
    print(f"Total departures in DB: {deps_count}")
    print(f"Agencies: {', '.join(agencies)}")
    print(f"\n✓ Database ready at {DB_PATH}")
    
    if deps_count < 100000:
        print(f"\n⚠️  We have {deps_count} departures, need 100k+ for full dataset")
        print("   Will need to fetch more data when rate limit resets")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

