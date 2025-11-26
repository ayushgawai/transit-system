#!/usr/bin/env python3
"""
Kafka Producer for Transit Data

This producer fetches data from TransitApp API and publishes to Kafka topics.
It's the streaming ingestion path for real-time data.

Topics:
- transit.departures  (real-time departure updates)
- transit.stops       (stop reference data)
- transit.alerts      (service alerts)

Usage:
    python kafka/transit_producer.py --continuous
    python kafka/transit_producer.py --once
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("⚠ kafka-python not installed. Install with: pip install kafka-python")

import yaml

# Import ingestion functions
import importlib.util
spec = importlib.util.spec_from_file_location(
    "transit_api_ingestion", 
    project_root / "ingestion" / "lambda" / "transit_api_ingestion.py"
)
transit_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transit_api)

fetch_nearby_stops = transit_api.fetch_nearby_stops
fetch_stop_departures = transit_api.fetch_stop_departures


# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# Topics
TOPIC_DEPARTURES = 'transit.departures'
TOPIC_STOPS = 'transit.stops'
TOPIC_ALERTS = 'transit.alerts'


def load_secrets() -> dict:
    """Load secrets from YAML."""
    secrets_path = project_root / "secrets.yaml"
    with open(secrets_path, 'r') as f:
        return yaml.safe_load(f)


def create_producer() -> 'KafkaProducer':
    """Create Kafka producer with JSON serialization."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        # Reliability settings
        acks='all',
        retries=3,
        # Performance
        batch_size=16384,
        linger_ms=10,
        compression_type='gzip'
    )


def produce_departures(producer: 'KafkaProducer', api_key: str, 
                       lat: float = 37.7749, lon: float = -122.4194) -> int:
    """Fetch and produce departure data to Kafka."""
    timestamp = datetime.utcnow().isoformat()
    produced = 0
    
    try:
        # Get nearby stops
        stops = fetch_nearby_stops(api_key, lat, lon, max_distance=1000)
        
        # Produce stops data
        stops_message = {
            'event_type': 'stops_update',
            'timestamp': timestamp,
            'location': {'lat': lat, 'lon': lon},
            'stops': stops,
            'stops_count': len(stops)
        }
        producer.send(
            TOPIC_STOPS, 
            key=f"{lat}_{lon}",
            value=stops_message
        )
        produced += 1
        
        # Get departures for each stop (limit to respect rate limits)
        for stop in stops[:5]:  # Max 5 stops per cycle
            stop_id = stop.get('global_stop_id')
            stop_name = stop.get('stop_name', stop_id)
            
            if not stop_id:
                continue
            
            try:
                departures = fetch_stop_departures(api_key, stop_id, max_num_departures=10)
                
                # Build message
                message = {
                    'event_type': 'departures_update',
                    'timestamp': timestamp,
                    'stop': stop,
                    'departures': departures
                }
                
                # Produce to Kafka
                future = producer.send(
                    TOPIC_DEPARTURES,
                    key=stop_id,
                    value=message
                )
                
                # Wait for send to complete
                future.get(timeout=10)
                produced += 1
                
                # Extract and produce alerts
                for route_dep in departures.get('route_departures', []):
                    for alert in route_dep.get('alerts', []):
                        alert_message = {
                            'event_type': 'alert',
                            'timestamp': timestamp,
                            'route_id': route_dep.get('global_route_id'),
                            'stop_id': stop_id,
                            'alert': alert
                        }
                        producer.send(TOPIC_ALERTS, key=stop_id, value=alert_message)
                
                # Small delay to respect rate limits
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ⚠ Error fetching departures for {stop_name}: {e}")
        
        # Flush to ensure all messages are sent
        producer.flush()
        
    except Exception as e:
        print(f"  ✗ Error in produce_departures: {e}")
    
    return produced


def run_producer(continuous: bool = False, interval: int = 60):
    """Run the Kafka producer."""
    print("=" * 60)
    print("Transit Kafka Producer")
    print("=" * 60)
    
    if not KAFKA_AVAILABLE:
        print("\n✗ kafka-python is required. Install with:")
        print("  pip install kafka-python")
        return
    
    # Load config
    print("\n📁 Loading configuration...")
    secrets = load_secrets()
    api_key = secrets.get('TRANSIT_APP_API_KEY')
    
    if not api_key:
        print("✗ TRANSIT_APP_API_KEY not found in secrets.yaml")
        return
    
    print(f"  ✓ API Key: {api_key[:10]}...")
    print(f"  ✓ Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    
    # Create producer
    print("\n🔗 Connecting to Kafka...")
    try:
        producer = create_producer()
        print("  ✓ Connected")
    except Exception as e:
        print(f"  ✗ Failed to connect: {e}")
        print("\n💡 Make sure Kafka is running:")
        print("   cd kafka && docker-compose up -d")
        return
    
    # Monitoring location (San Francisco)
    lat, lon = 37.7749, -122.4194
    
    print(f"\n📍 Monitoring location: ({lat}, {lon})")
    print(f"📡 Topics: {TOPIC_DEPARTURES}, {TOPIC_STOPS}, {TOPIC_ALERTS}")
    
    if continuous:
        print(f"\n🔄 Running continuously (every {interval}s). Press Ctrl+C to stop.\n")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                print(f"[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                count = produce_departures(producer, api_key, lat, lon)
                print(f"  ✓ Produced {count} messages")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n⏹ Stopping producer...")
                break
    else:
        print("\n🚀 Running single fetch...")
        count = produce_departures(producer, api_key, lat, lon)
        print(f"\n✓ Produced {count} messages")
    
    # Cleanup
    producer.close()
    print("\n✓ Producer closed")


def main():
    parser = argparse.ArgumentParser(description='Transit Kafka Producer')
    parser.add_argument('--continuous', action='store_true', 
                        help='Run continuously')
    parser.add_argument('--interval', type=int, default=60,
                        help='Seconds between fetches (default: 60)')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit')
    args = parser.parse_args()
    
    continuous = args.continuous and not args.once
    run_producer(continuous=continuous, interval=args.interval)


if __name__ == "__main__":
    main()

