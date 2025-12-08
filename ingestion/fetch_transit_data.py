"""
Fetch Real Transit Data from TransitApp API
Fetches data for VTA buses, BART, and trams (if available)
Only fetches data we actually have - no fake data
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load secrets
def load_secrets() -> dict:
    """Load secrets from secrets.yaml"""
    secrets_path = project_root / "secrets.yaml"
    if not secrets_path.exists():
        raise FileNotFoundError(f"secrets.yaml not found at {secrets_path}")
    
    with open(secrets_path, 'r') as f:
        return yaml.safe_load(f) or {}


def call_transitapp_api(api_key: str, endpoint: str, params: Dict[str, Any] = None, retry_count: int = 3) -> Dict[str, Any]:
    """Call TransitApp API v3 with rate limit handling"""
    base_url = "https://external.transitapp.com/v3"
    url = f"{base_url}/{endpoint}"
    
    headers = {
        "apiKey": api_key,
        "Accept-Language": "en",
        "Content-Type": "application/json"
    }
    
    params = params.copy() if params else {}
    
    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Handle rate limiting (429)
            if response.status_code == 429:
                if attempt < retry_count - 1:
                    wait_time = 60 * (attempt + 1)  # Wait 60s, 120s, 180s
                    print(f"   ⚠️  Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{retry_count}...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise requests.exceptions.HTTPError(f"Rate limit exceeded after {retry_count} attempts")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < retry_count - 1 and hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                wait_time = 60 * (attempt + 1)
                print(f"   ⚠️  Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{retry_count}...")
                time.sleep(wait_time)
                continue
            
            print(f"API call failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text[:500]}")
            raise
    
    raise Exception("Failed to call API after retries")


def fetch_nearby_stops(api_key: str, lat: float, lon: float, max_distance: int = 2000) -> List[Dict]:
    """Fetch nearby stops from TransitApp API"""
    params = {
        "lat": lat,
        "lon": lon,
        "max_distance": max_distance
    }
    response = call_transitapp_api(api_key, "public/nearby_stops", params)
    return response.get("stops", [])


def fetch_stop_departures(api_key: str, global_stop_id: str, max_num_departures: int = 10) -> Dict[str, Any]:
    """Fetch real-time departures for a specific stop"""
    params = {
        "global_stop_id": global_stop_id,
        "max_num_departures": max(1, min(10, max_num_departures)),
        "should_update_realtime": "true"
    }
    response = call_transitapp_api(api_key, "public/stop_departures", params)
    return response


def get_agency_from_stop(stop: Dict) -> str:
    """Extract agency name from stop data"""
    agencies = stop.get("agencies", [])
    if agencies:
        return agencies[0].get("name", "UNKNOWN")
    
    # Try to extract from global_stop_id (format: "AGENCY:STOP_ID")
    global_stop_id = stop.get("global_stop_id", "")
    if ":" in global_stop_id:
        return global_stop_id.split(":")[0]
    
    return "UNKNOWN"


def filter_stops_by_agency(stops: List[Dict], target_agencies: List[str]) -> Dict[str, List[Dict]]:
    """Filter stops by agency and group them"""
    filtered = {agency: [] for agency in target_agencies}
    filtered["OTHER"] = []
    
    for stop in stops:
        agency = get_agency_from_stop(stop)
        agency_upper = agency.upper()
        
        # Check if this stop belongs to any target agency
        found = False
        for target in target_agencies:
            if target.upper() in agency_upper or agency_upper in target.upper():
                filtered[target].append(stop)
                found = True
                break
        
        if not found:
            filtered["OTHER"].append(stop)
    
    return filtered


def fetch_data_for_location(api_key: str, location_name: str, lat: float, lon: float, 
                           target_agencies: List[str], output_dir: Path) -> Dict[str, Any]:
    """Fetch data for a specific location"""
    print(f"\n{'='*60}")
    print(f"Fetching data for {location_name} ({lat}, {lon})")
    print(f"Target agencies: {', '.join(target_agencies)}")
    print(f"{'='*60}")
    
    # Fetch nearby stops (with rate limiting)
    print(f"\n1. Fetching nearby stops (max_distance=2000m)...")
    print(f"   (Rate limit: 5 calls/min, waiting 15s between locations...)")
    time.sleep(15)  # Wait between location fetches to respect rate limit
    stops = fetch_nearby_stops(api_key, lat, lon, max_distance=2000)
    print(f"   ✓ Found {len(stops)} total stops")
    
    if not stops:
        print(f"   ⚠️  No stops found for {location_name}")
        return {"location": location_name, "stops": [], "departures": {}, "agencies": {}}
    
    # Filter stops by agency
    print(f"\n2. Filtering stops by agency...")
    filtered_stops = filter_stops_by_agency(stops, target_agencies)
    
    agency_counts = {k: len(v) for k, v in filtered_stops.items() if k != "OTHER"}
    print(f"   Agency breakdown:")
    for agency, count in agency_counts.items():
        print(f"     - {agency}: {count} stops")
    if filtered_stops.get("OTHER"):
        print(f"     - OTHER: {len(filtered_stops['OTHER'])} stops")
    
    # Save stops data
    timestamp = datetime.utcnow().isoformat()
    stops_data = {
        "location": {"name": location_name, "lat": lat, "lon": lon},
        "timestamp": timestamp,
        "stops": stops,
        "filtered_by_agency": {k: len(v) for k, v in filtered_stops.items()}
    }
    
    stops_file = output_dir / f"stops_{location_name.lower().replace(' ', '_')}_{timestamp.replace(':', '-').split('.')[0]}.json"
    stops_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stops_file, 'w') as f:
        json.dump(stops_data, f, indent=2, default=str)
    print(f"   ✓ Saved stops to {stops_file}")
    
    # Fetch departures for stops from target agencies
    print(f"\n3. Fetching departures for target agency stops...")
    departures_data = {}
    total_departures = 0
    
    # Collect all stops from target agencies
    all_target_stops = []
    for agency in target_agencies:
        all_target_stops.extend(filtered_stops.get(agency, []))
    
    print(f"   Fetching departures for {len(all_target_stops)} stops...")
    
    for i, stop in enumerate(all_target_stops, 1):
        stop_id = stop.get("global_stop_id")
        stop_name = stop.get("stop_name", "Unknown")
        agency = get_agency_from_stop(stop)
        
        if not stop_id:
            continue
        
        try:
            print(f"   [{i}/{len(all_target_stops)}] Fetching {stop_name} ({agency})...", end=" ")
            departures = fetch_stop_departures(api_key, stop_id, max_num_departures=10)
            
            # Count departures
            route_departures = departures.get("route_departures", [])
            dep_count = sum(
                len(rd.get("itineraries", [{}])[0].get("schedule_items", []))
                for rd in route_departures
            )
            total_departures += dep_count
            
            departures_data[stop_id] = {
                "stop": stop,
                "departures": departures,
                "departure_count": dep_count
            }
            
            print(f"✓ {dep_count} departures")
            
            # Rate limiting: TransitApp API allows 5 calls/minute = 1 call per 12 seconds
            if i < len(all_target_stops):
                time.sleep(13)  # Wait 13 seconds between calls to be safe
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            continue
    
    print(f"\n   ✓ Total departures fetched: {total_departures}")
    
    # Save departures data
    if departures_data:
        deps_file = output_dir / f"departures_{location_name.lower().replace(' ', '_')}_{timestamp.replace(':', '-').split('.')[0]}.json"
        deps_data = {
            "location": {"name": location_name, "lat": lat, "lon": lon},
            "timestamp": timestamp,
            "departures": departures_data,
            "total_departures": total_departures
        }
        with open(deps_file, 'w') as f:
            json.dump(deps_data, f, indent=2, default=str)
        print(f"   ✓ Saved departures to {deps_file}")
    
    # Analyze agencies found
    agencies_found = {}
    for stop in stops:
        agency = get_agency_from_stop(stop)
        if agency not in agencies_found:
            agencies_found[agency] = 0
        agencies_found[agency] += 1
    
    return {
        "location": location_name,
        "total_stops": len(stops),
        "target_agency_stops": {k: len(v) for k, v in filtered_stops.items() if k != "OTHER"},
        "total_departures": total_departures,
        "agencies_found": agencies_found,
        "stops_file": str(stops_file),
        "departures_file": str(deps_file) if departures_data else None
    }


def main():
    """Main function to fetch transit data"""
    print("="*60)
    print("Transit Data Fetcher - Real Data Only")
    print("="*60)
    
    # Load secrets
    try:
        secrets = load_secrets()
        api_key = secrets.get("TRANSIT_APP_API_KEY")
        if not api_key:
            raise ValueError("TRANSIT_APP_API_KEY not found in secrets.yaml")
        print(f"\n✓ API key loaded: {api_key[:10]}...")
    except Exception as e:
        print(f"\n✗ Error loading secrets: {e}")
        return 1
    
    # Define locations and target agencies
    locations = [
        {
            "name": "San Jose",
            "lat": 37.3382,
            "lon": -121.8863,
            "agencies": ["VTA"]  # VTA buses
        },
        {
            "name": "San Francisco Bay Area",
            "lat": 37.7749,
            "lon": -122.4194,
            "agencies": ["BART"]  # BART
        },
        {
            "name": "San Francisco",
            "lat": 37.7749,
            "lon": -122.4194,
            "agencies": ["MUNI", "SFMTA"]  # Trams/light rail
        }
    ]
    
    # Create output directory
    output_base = project_root / "ingestion" / "data" / "local_test" / "transitapp" / "real_data"
    output_base.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Fetch data for each location
    for loc in locations:
        try:
            result = fetch_data_for_location(
                api_key=api_key,
                location_name=loc["name"],
                lat=loc["lat"],
                lon=loc["lon"],
                target_agencies=loc["agencies"],
                output_dir=output_base
            )
            results.append(result)
        except Exception as e:
            print(f"\n✗ Error fetching data for {loc['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print("\n" + "="*60)
    print("FETCH SUMMARY")
    print("="*60)
    
    total_stops = 0
    total_departures = 0
    
    for result in results:
        print(f"\n{result['location']}:")
        print(f"  Total stops found: {result['total_stops']}")
        print(f"  Target agency stops: {result['target_agency_stops']}")
        print(f"  Total departures: {result['total_departures']}")
        print(f"  Agencies found: {list(result['agencies_found'].keys())[:5]}...")
        total_stops += result['total_stops']
        total_departures += result['total_departures']
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_stops} stops, {total_departures} departures")
    print(f"{'='*60}")
    
    # Save summary
    summary_file = output_base / f"fetch_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
            "totals": {
                "stops": total_stops,
                "departures": total_departures
            }
        }, f, indent=2, default=str)
    
    print(f"\n✓ Summary saved to {summary_file}")
    print("\nNext steps:")
    print("1. Review the fetched data to understand structure")
    print("2. Analyze what agencies/data we actually have")
    print("3. Build data pipeline based on real data structure")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

