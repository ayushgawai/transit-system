#!/usr/bin/env python3
"""
Kafka Consumer for Transit Data → Snowflake

This consumer reads from Kafka topics and writes to Snowflake RAW tables.
It provides the streaming bridge between Kafka and the data warehouse.

Usage:
    python kafka/transit_consumer.py
    python kafka/transit_consumer.py --batch-size 100 --timeout 30
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("⚠ kafka-python not installed. Install with: pip install kafka-python")

import yaml
import snowflake.connector


# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
CONSUMER_GROUP = 'transit-snowflake-consumer'

# Topics
TOPIC_DEPARTURES = 'transit.departures'
TOPIC_STOPS = 'transit.stops'
TOPIC_ALERTS = 'transit.alerts'


def load_secrets() -> dict:
    """Load secrets from YAML."""
    secrets_path = project_root / "secrets.yaml"
    with open(secrets_path, 'r') as f:
        return yaml.safe_load(f)


def get_snowflake_connection(secrets: dict):
    """Create Snowflake connection."""
    return snowflake.connector.connect(
        account=secrets['SNOWFLAKE_ACCOUNT'],
        user=secrets['SNOWFLAKE_USER'],
        password=secrets['SNOWFLAKE_PASSWORD'],
        warehouse=secrets['SNOWFLAKE_WAREHOUSE'],
        database=secrets['SNOWFLAKE_DATABASE'],
        role=secrets['SNOWFLAKE_ROLE']
    )


def create_consumer(topics: List[str]) -> 'KafkaConsumer':
    """Create Kafka consumer."""
    return KafkaConsumer(
        *topics,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='earliest',  # Start from beginning if no offset
        enable_auto_commit=True,
        auto_commit_interval_ms=5000,
        # Consumer config
        max_poll_records=100,
        session_timeout_ms=30000
    )


def write_departures_to_snowflake(conn, messages: List[Dict]) -> int:
    """Write departure messages to Snowflake."""
    if not messages:
        return 0
    
    cursor = conn.cursor()
    loaded = 0
    
    for msg in messages:
        try:
            # Extract data
            timestamp = msg.get('timestamp', datetime.utcnow().isoformat())
            stop = msg.get('stop', {})
            stop_global_id = stop.get('global_stop_id', '')
            stop_name = stop.get('stop_name', '')
            
            # Full message as JSON
            raw_json = json.dumps(msg)
            
            cursor.execute("""
                INSERT INTO RAW.TRANSIT_DEPARTURES 
                (source_file, raw_json, stop_global_id, stop_name, fetch_timestamp)
                SELECT 
                    'kafka:transit.departures',
                    PARSE_JSON(%s),
                    %s,
                    %s,
                    TRY_TO_TIMESTAMP_NTZ(%s)
            """, (raw_json, stop_global_id, stop_name, timestamp))
            
            loaded += 1
            
        except Exception as e:
            print(f"  ⚠ Error inserting departure: {e}")
    
    cursor.close()
    return loaded


def write_stops_to_snowflake(conn, messages: List[Dict]) -> int:
    """Write stops messages to Snowflake."""
    if not messages:
        return 0
    
    cursor = conn.cursor()
    loaded = 0
    
    for msg in messages:
        try:
            location = msg.get('location', {})
            stops = msg.get('stops', [])
            
            raw_data = {'stops': stops}
            raw_json = json.dumps(raw_data)
            
            cursor.execute("""
                INSERT INTO RAW.TRANSIT_STOPS 
                (source_file, raw_json, location_lat, location_lon, stops_count, fetch_timestamp)
                SELECT 
                    'kafka:transit.stops',
                    PARSE_JSON(%s),
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP()
            """, (raw_json, location.get('lat', 0), location.get('lon', 0), len(stops)))
            
            loaded += 1
            
        except Exception as e:
            print(f"  ⚠ Error inserting stops: {e}")
    
    cursor.close()
    return loaded


def run_consumer(batch_size: int = 100, timeout_seconds: int = 30):
    """Run the Kafka consumer."""
    print("=" * 60)
    print("Transit Kafka Consumer → Snowflake")
    print("=" * 60)
    
    if not KAFKA_AVAILABLE:
        print("\n✗ kafka-python is required. Install with:")
        print("  pip install kafka-python")
        return
    
    # Load config
    print("\n📁 Loading configuration...")
    secrets = load_secrets()
    
    # Connect to Snowflake
    print("\n🔗 Connecting to Snowflake...")
    try:
        sf_conn = get_snowflake_connection(secrets)
        print(f"  ✓ Connected to {secrets['SNOWFLAKE_DATABASE']}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return
    
    # Create consumer
    print(f"\n🔗 Connecting to Kafka...")
    topics = [TOPIC_DEPARTURES, TOPIC_STOPS, TOPIC_ALERTS]
    try:
        consumer = create_consumer(topics)
        print(f"  ✓ Subscribed to: {', '.join(topics)}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        print("\n💡 Make sure Kafka is running:")
        print("   cd kafka && docker-compose up -d")
        return
    
    print(f"\n📥 Consuming messages (batch={batch_size}, timeout={timeout_seconds}s)")
    print("   Press Ctrl+C to stop.\n")
    
    # Message buffers
    departure_buffer = []
    stops_buffer = []
    total_processed = 0
    
    try:
        while True:
            # Poll for messages
            messages = consumer.poll(timeout_ms=timeout_seconds * 1000, max_records=batch_size)
            
            if not messages:
                print(f"  ... waiting for messages (processed {total_processed} total)")
                continue
            
            # Process messages by topic
            for topic_partition, records in messages.items():
                topic = topic_partition.topic
                
                for record in records:
                    if topic == TOPIC_DEPARTURES:
                        departure_buffer.append(record.value)
                    elif topic == TOPIC_STOPS:
                        stops_buffer.append(record.value)
                    # Alerts can be extracted from departures
            
            # Write to Snowflake if buffer is full
            if len(departure_buffer) >= batch_size:
                count = write_departures_to_snowflake(sf_conn, departure_buffer)
                print(f"  ✓ Wrote {count} departures to Snowflake")
                total_processed += count
                departure_buffer = []
            
            if len(stops_buffer) >= 10:  # Stops update less frequently
                count = write_stops_to_snowflake(sf_conn, stops_buffer)
                print(f"  ✓ Wrote {count} stops updates to Snowflake")
                total_processed += count
                stops_buffer = []
    
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping consumer...")
        
        # Flush remaining buffers
        if departure_buffer:
            count = write_departures_to_snowflake(sf_conn, departure_buffer)
            total_processed += count
            print(f"  ✓ Flushed {count} departures")
        
        if stops_buffer:
            count = write_stops_to_snowflake(sf_conn, stops_buffer)
            total_processed += count
            print(f"  ✓ Flushed {count} stops")
    
    finally:
        consumer.close()
        sf_conn.close()
        print(f"\n✓ Processed {total_processed} total messages")


def main():
    parser = argparse.ArgumentParser(description='Transit Kafka Consumer')
    parser.add_argument('--batch-size', type=int, default=100,
                        help='Messages per batch (default: 100)')
    parser.add_argument('--timeout', type=int, default=30,
                        help='Poll timeout in seconds (default: 30)')
    args = parser.parse_args()
    
    run_consumer(batch_size=args.batch_size, timeout_seconds=args.timeout)


if __name__ == "__main__":
    main()

