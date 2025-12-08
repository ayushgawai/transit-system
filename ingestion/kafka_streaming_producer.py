"""
Kafka Streaming Producer
Continuously fetches data from Transit API and sends to Kafka
"""
import sys
from pathlib import Path
import os
import time
import json
from datetime import datetime
from kafka import KafkaProducer
import requests

# Calculate project root - works in both container and local
if os.path.exists('/opt/airflow'):
    project_root = Path('/opt/airflow')
else:
    project_root = Path(__file__).parent.parent

sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config

def get_transit_api_key():
    """Get Transit API key from config"""
    config = get_warehouse_config()
    return config.get_transit_api_key()

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

def create_kafka_producer(bootstrap_servers: str = 'localhost:9092'):
    """Create Kafka producer"""
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )

def stream_transit_data():
    """Main streaming function"""
    config = get_warehouse_config()
    
    if not config.is_streaming_enabled():
        print("Streaming is disabled in config")
        return
    
    api_key = get_transit_api_key()
    if not api_key:
        print("❌ Transit API key not found")
        return
    
    # Create Kafka producer
    kafka_config = config.config.get('kafka', {})
    bootstrap_servers = kafka_config.get('bootstrap_servers', 'localhost:9092')
    topic = kafka_config.get('topics', {}).get('streaming', 'transit-streaming')
    
    try:
        producer = create_kafka_producer(bootstrap_servers)
        print(f"✅ Connected to Kafka at {bootstrap_servers}")
    except Exception as e:
        print(f"❌ Failed to connect to Kafka: {e}")
        return
    
    # Monitoring locations
    locations = [
        (37.7749, -122.4194, "San Francisco"),  # BART
        (37.3382, -121.8863, "San Jose"),  # VTA
    ]
    
    print("=" * 70)
    print("🔄 Starting Transit API Streaming to Kafka")
    print("=" * 70)
    print(f"Topic: {topic}")
    print(f"Polling interval: 60 seconds")
    print()
    
    message_count = 0
    
    try:
        while True:
            for lat, lon, city in locations:
                print(f"\n📍 Fetching stops near {city}...")
                stops = fetch_nearby_stops(api_key, lat, lon, max_distance=1500)
                
                if not stops:
                    print(f"  ⚠ No stops found")
                    continue
                
                # Limit to first 1 stop per location to respect rate limits (5 calls/min)
                for stop in stops[:1]:
                    stop_id = stop.get('global_stop_id')
                    stop_name = stop.get('stop_name', stop.get('name', 'Unknown'))
                    
                    if not stop_id:
                        continue
                    
                    print(f"  Fetching departures for {stop_name} ({stop_id})...")
                    
                    try:
                        deps_data = fetch_stop_departures(api_key, stop_id, max_num_departures=8)
                        
                        if not deps_data:
                            print(f"    ⚠ No departures data returned")
                            continue
                        
                        # Parse and send to Kafka
                        # API structure: {"departures": {"route_departures": [...]}}
                        departures = deps_data.get('departures', {})
                        route_departures = departures.get('route_departures', [])
                        
                        if not route_departures:
                            print(f"    ⚠ No route departures found")
                            continue
                        
                        print(f"    ✅ Found {len(route_departures)} route departures")
                        
                        for route_dep in route_departures:
                            # Route info is directly in route_dep, not nested
                            global_route_id = route_dep.get('global_route_id', '')
                            route_short_name = route_dep.get('route_short_name', '')
                            route_long_name = route_dep.get('route_long_name', '')
                            
                            # Infer agency from route ID
                            agency = 'Unknown'
                            if global_route_id:
                                if global_route_id.startswith('BART:'):
                                    agency = 'BART'
                                elif global_route_id.startswith('VTA:') or global_route_id.startswith('VTA'):
                                    agency = 'VTA'
                                elif global_route_id.startswith('MUNI:'):
                                    agency = 'MUNI'
                            
                            # Process itineraries
                            itineraries = route_dep.get('itineraries', [])
                            for itinerary in itineraries:
                                schedule_items = itinerary.get('schedule_items', [])
                                
                                if not schedule_items:
                                    continue
                                
                                for item in schedule_items:
                                    # Create message
                                    scheduled_time = item.get('scheduled_departure_time')
                                    actual_time = item.get('departure_time')
                                    
                                    message = {
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'global_stop_id': stop_id,
                                        'stop_name': stop_name,
                                        'global_route_id': global_route_id,
                                        'route_short_name': route_short_name,
                                        'route_long_name': route_long_name,
                                        'agency': agency,
                                        'city': city,
                                        'scheduled_departure_time': scheduled_time,
                                        'departure_time': actual_time,
                                        'is_real_time': bool(item.get('is_real_time', False)),
                                        'trip_search_key': item.get('trip_search_key', ''),
                                        'delay_seconds': None
                                    }
                                    
                                    # Calculate delay (only for real-time data)
                                    if message['is_real_time'] and scheduled_time and actual_time:
                                        message['delay_seconds'] = int(actual_time - scheduled_time)
                                    
                                    # Send to Kafka
                                    key = f"{stop_id}_{global_route_id}_{item.get('trip_search_key', '')}"
                                    producer.send(topic, key=key, value=message)
                                    message_count += 1
                                    
                                    if message_count % 10 == 0:
                                        print(f"  📤 Sent {message_count} messages to Kafka")
                        
                    except Exception as e:
                        print(f"    ⚠ Error: {e}")
                        if "429" in str(e) or "Too Many Requests" in str(e):
                            print("    ⚠ Rate limit hit, waiting...")
                            time.sleep(60)
                            break
                    
                    time.sleep(15)  # Rate limiting - wait 15s between stops (4 calls/min max)
            
            print(f"\n✅ Total messages sent: {message_count}")
            print("⏳ Waiting 90 seconds before next poll...")
            time.sleep(90)  # Wait longer to respect rate limits
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping streaming...")
    finally:
        producer.close()
        print(f"✅ Streaming stopped. Total messages: {message_count}")

if __name__ == "__main__":
    stream_transit_data()

