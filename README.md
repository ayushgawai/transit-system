# Transit Service Reliability & Demand Planning System

MSDA Capstone Project - Production-capable prototype for metropolitan transit operators.

## Architecture

### Components

1. **Config System** (`config.yaml`)
   - Warehouse selection: Redshift (default) or Snowflake
   - AWS Secrets Manager integration for credentials
   - Single configuration file for all settings

2. **Airflow** (Local Docker)
   - `gtfs_incremental_ingestion`: GTFS data ingestion (every 6 hours)
   - `transit_streaming`: Kafka streaming pipeline (every hour)
   - `ml_forecast`: ML forecasting (every 6 hours)

3. **Kafka** (Local Docker)
   - Producer: Fetches Transit API data → Kafka topic
   - Consumer: Kafka topic → Landing tables

4. **DBT**
   - Landing → Raw: GTFS staging models
   - Streaming → Analytics: Real-time data staging
   - Transform: Route departures
   - Analytics: Performance metrics
   - Supports Redshift and Snowflake

5. **Backend API** (FastAPI)
   - Uses warehouse config for connections
   - Serves data to frontend

6. **Frontend** (React)
   - Dashboard, Analytics, Maps, Forecasts
   - Real-time data visualization

## Data Flow

```
GTFS Feeds → Landing Tables → (dbt) → Raw Tables → (dbt) → Analytics Tables
                                                              ↑
Transit API → Kafka → Landing Tables → (dbt) → Analytics Tables
                                                              ↓
                                                      ML Forecasts
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- AWS CLI configured with profile `transit-system`
- Redshift cluster (or Snowflake account)

### 1. Configure Warehouse

Edit `config.yaml`:

```yaml
warehouse:
  type: 'redshift'  # or 'snowflake'
```

For Redshift, store credentials in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name transit/redshift-dev \
  --secret-string '{"host":"your-cluster.region.redshift.amazonaws.com","port":5439,"user":"awsuser","password":"your-password","database":"transit_db"}'
```

For Snowflake, credentials should already be in Secrets Manager as `transit/snowflake-dev`.

### 2. Start Services

```bash
./start_local.sh
```

This starts:
- Kafka and Zookeeper
- Airflow (webserver + scheduler)

### 3. Access Services

- **Airflow UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin`

- **Backend API**: http://localhost:8000
  - Docs: http://localhost:8000/docs

- **Frontend**: http://localhost:3000 (if running)

### 4. Run Initial Data Load

In Airflow UI:
1. Find `gtfs_incremental_ingestion` DAG
2. Trigger manually
3. This loads GTFS data from Aug 1, 2025 onwards

### 5. Start Streaming

In Airflow UI:
1. Find `transit_streaming` DAG
2. Trigger manually (or wait for hourly schedule)
3. This starts Kafka producer and consumer

## Configuration

### Warehouse Selection

Set `warehouse.type` in `config.yaml`:
- `redshift`: Use Amazon Redshift (default)
- `snowflake`: Use Snowflake

### GTFS Initial Load

First run loads data from `initial_load_date` (default: 2025-08-01).
Subsequent runs are incremental (only new data).

### Streaming

Streaming is enabled by default. Set `data_sources.transit_api.streaming_enabled: false` to disable.

## DBT Models

### Run DBT

```bash
cd dbt/transit_dbt

# For Redshift
dbt run --target redshift

# For Snowflake
dbt run --target snowflake
```

### Model Structure

- **Landing**: Raw GTFS and streaming data
- **Raw**: Staged GTFS data (stops, routes, trips, stop_times)
- **Transform**: Combined route departures
- **Analytics**: Performance metrics

## Testing

### Test Kafka

```bash
# Producer
python ingestion/kafka_streaming_producer.py

# Consumer
python ingestion/kafka_consumer_to_landing.py
```

### Test GTFS Load

```bash
python ingestion/fetch_gtfs_incremental.py
```

### Test Backend

```bash
cd api
uvicorn main:app --reload
```

Visit: http://localhost:8000/docs

## Technologies

- **Streaming**: Kafka (Producer + Consumer)
- **ETL**: DBT (Landing → Raw → Transform → Analytics)
- **Orchestration**: Airflow (3 DAGs)
- **AWS**: Secrets Manager (credentials)
- **Data Warehouse**: Redshift (default) or Snowflake
- **ML**: Forecasting (Snowflake ML or Local)

## Troubleshooting

### Kafka not starting

```bash
docker-compose -f docker-compose.local.yml restart kafka zookeeper
```

### Airflow not starting

```bash
docker-compose -f docker-compose.local.yml --profile local down -v
docker-compose -f docker-compose.local.yml --profile local up -d
```

### Warehouse connection errors

- Check `config.yaml` warehouse type
- Verify credentials in AWS Secrets Manager
- Check `dbt/transit_dbt/profiles.yml` target configuration

## Stopping Services

```bash
docker-compose -f docker-compose.local.yml --profile local down
```
