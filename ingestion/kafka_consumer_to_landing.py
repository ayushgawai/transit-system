"""
Kafka Consumer to Landing Tables
Consumes messages from Kafka and loads into landing tables
"""
import sys
from pathlib import Path
import os
import json
import hashlib
from datetime import datetime
from kafka import KafkaConsumer
import time

# Calculate project root - works in both container and local
if os.path.exists('/opt/airflow'):
    project_root = Path('/opt/airflow')
else:
    project_root = Path(__file__).parent.parent

sys.path.insert(0, str(project_root))

from config.warehouse_config import get_warehouse_config
from api.warehouse_connection import get_warehouse_connection

def init_streaming_landing_table_snowflake():
    """Initialize streaming landing table in Snowflake"""
    config = get_warehouse_config()
    if not config.is_snowflake():
        raise ValueError("Only Snowflake is supported")
    
    sf_config = config.get_snowflake_config()
    schema = sf_config.get('schema', 'ANALYTICS')
    
    with get_warehouse_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        
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
        print("✓ Streaming landing table initialized in Snowflake")

def consume_and_load():
    """Consume from Kafka and load to landing table"""
    config = get_warehouse_config()
    
    # Initialize Snowflake table
    init_streaming_landing_table_snowflake()
    
    kafka_config = config.config.get('kafka', {})
    
    bootstrap_servers = kafka_config.get('bootstrap_servers', 'localhost:9092')
    topic = kafka_config.get('topics', {}).get('streaming', 'transit-streaming')
    consumer_group = kafka_config.get('consumer_group', 'transit-consumers')
    
    print("=" * 70)
    print("📥 Kafka Consumer → Landing Tables")
    print("=" * 70)
    print(f"Kafka: {bootstrap_servers}")
    print(f"Topic: {topic}")
    print(f"Consumer Group: {consumer_group}")
    print()
    
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=consumer_group,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        print("✅ Connected to Kafka")
    except Exception as e:
        print(f"❌ Failed to connect to Kafka: {e}")
        return
    
    sf_config = config.get_snowflake_config()
    schema = sf_config.get('schema', 'ANALYTICS')
    
    message_count = 0
    batch_size = 100
    batch_data = []
    
    try:
        print("🔄 Consuming messages...")
        with get_warehouse_connection() as conn:
            cursor = conn.cursor()
            
            for message in consumer:
                try:
                    data = message.value
                    
                    # Generate unique ID
                    id_str = f"{data.get('global_stop_id', '')}_{data.get('global_route_id', '')}_{data.get('trip_search_key', '')}_{data.get('timestamp', '')}"
                    record_id = hashlib.md5(id_str.encode()).hexdigest()
                    
                    batch_data.append((
                        record_id,
                        data.get('timestamp'),
                        data.get('global_stop_id'),
                        data.get('stop_name'),
                        data.get('global_route_id'),
                        data.get('route_short_name'),
                        data.get('route_long_name'),
                        data.get('agency'),
                        data.get('city'),
                        data.get('scheduled_departure_time'),
                        data.get('departure_time'),
                        data.get('is_real_time', False),
                        data.get('trip_search_key'),
                        data.get('delay_seconds')
                    ))
                    
                    message_count += 1
                    
                    if len(batch_data) >= batch_size:
                        cursor.executemany(f"""
                            INSERT INTO {schema}.LANDING_STREAMING_DEPARTURES
                            (ID, TIMESTAMP, GLOBAL_STOP_ID, STOP_NAME, GLOBAL_ROUTE_ID,
                             ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY, CITY,
                             SCHEDULED_DEPARTURE_TIME, DEPARTURE_TIME, IS_REAL_TIME,
                             TRIP_SEARCH_KEY, DELAY_SECONDS)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, batch_data)
                        conn.commit()
                        batch_data = []
                        print(f"  ✅ Loaded {message_count} messages to landing table")
                
                except Exception as e:
                    print(f"  ⚠ Error processing message: {e}")
                    continue
            
            # Insert remaining batch
            if batch_data:
                cursor.executemany(f"""
                    INSERT INTO {schema}.LANDING_STREAMING_DEPARTURES
                    (ID, TIMESTAMP, GLOBAL_STOP_ID, STOP_NAME, GLOBAL_ROUTE_ID,
                     ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY, CITY,
                     SCHEDULED_DEPARTURE_TIME, DEPARTURE_TIME, IS_REAL_TIME,
                     TRIP_SEARCH_KEY, DELAY_SECONDS)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, batch_data)
                conn.commit()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping consumer...")
    finally:
        consumer.close()
        print(f"✅ Consumer stopped. Total messages: {message_count}")

if __name__ == "__main__":
    consume_and_load()

