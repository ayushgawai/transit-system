# Kafka Streaming Setup

This directory contains the Kafka streaming infrastructure for real-time transit data.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ TransitApp  │────▶│   Kafka     │────▶│  Consumer   │────▶│  Snowflake  │
│    API      │     │  Producer   │     │  (Python)   │     │    RAW      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Kafka Topics│
                    │ - departures│
                    │ - stops     │
                    │ - alerts    │
                    └─────────────┘
```

## Quick Start

### 1. Start Kafka (Docker)

```bash
cd kafka
docker-compose up -d
```

This starts:
- **Zookeeper** on port 2181
- **Kafka** on port 9092
- **Kafka UI** on port 8090 (http://localhost:8090)

### 2. Install Python Dependencies

```bash
pip install kafka-python
```

### 3. Run Producer (Fetches from API → Kafka)

```bash
# Single fetch
python kafka/transit_producer.py --once

# Continuous (every 60 seconds)
python kafka/transit_producer.py --continuous --interval 60
```

### 4. Run Consumer (Kafka → Snowflake)

```bash
python kafka/transit_consumer.py
```

## Kafka Topics

| Topic | Description | Key |
|-------|-------------|-----|
| `transit.departures` | Real-time departure updates | `stop_global_id` |
| `transit.stops` | Stop/station data | `lat_lon` |
| `transit.alerts` | Service alerts | `stop_global_id` |

## Kafka UI

Access the Kafka UI at: **http://localhost:8090**

Features:
- View topics and messages
- Monitor consumer groups
- Check broker status

## Configuration

Environment variables:
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address (default: `localhost:9092`)

## Stopping Kafka

```bash
cd kafka
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```

## Troubleshooting

### Kafka not connecting?
```bash
# Check if containers are running
docker ps

# View logs
docker-compose logs kafka
```

### Producer fails to connect?
Make sure Kafka is running:
```bash
docker-compose up -d
```

### Consumer lag?
Check consumer group status in Kafka UI (http://localhost:8090)

## Production Notes

For AWS deployment, consider:
1. **Amazon MSK** (Managed Streaming for Kafka)
2. **Confluent Cloud** (free tier available)
3. **Self-hosted on EC2** (more control, more work)

The same producer/consumer code works with any Kafka cluster - just update `KAFKA_BOOTSTRAP_SERVERS`.

