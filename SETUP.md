# Complete Setup Guide

This guide will help you set up the Transit System on a fresh Mac after cloning the repository.

## Prerequisites

Before starting, ensure you have the following installed:

1. **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
   - Verify: `docker --version`
   - Make sure Docker Desktop is running

2. **Python 3.9+** - Usually pre-installed on Mac
   - Verify: `python3 --version`
   - If not installed: `brew install python3`

3. **Node.js 18+** and npm
   - Verify: `node --version` and `npm --version`
   - If not installed: `brew install node`

4. **AWS CLI** - For Secrets Manager access
   - Verify: `aws --version`
   - If not installed: `brew install awscli`
   - Configure: `aws configure --profile transit-system`

5. **Git** - Usually pre-installed
   - Verify: `git --version`

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd transit-system
```

### 2. Configure AWS Secrets Manager

The system uses AWS Secrets Manager for secure credential storage. You need to set up two secrets:

#### Snowflake Credentials

```bash
aws secretsmanager create-secret \
  --name transit/snowflake-dev \
  --profile transit-system \
  --secret-string '{
    "account": "your-account.us-west-2",
    "user": "your-username",
    "password": "your-password",
    "warehouse": "HORNET_QUERY_WH",
    "database": "USER_DB_HORNET",
    "role": "TRAINING_ROLE"
  }'
```

#### Perplexity API Key (for LLM chat feature)

```bash
aws secretsmanager create-secret \
  --name transit/perplexity \
  --profile transit-system \
  --secret-string '{
    "api_key": "your-perplexity-api-key"
  }'
```

**Note**: If you don't have AWS Secrets Manager access, you can create a local `secrets.yaml` file (see Alternative Setup below).

### 3. Set Up dbt Environment Variables (Optional)

If you want to run dbt manually, set these environment variables:

```bash
export SNOWFLAKE_ACCOUNT="your-account.us-west-2"
export SNOWFLAKE_USER="your-username"
export SNOWFLAKE_PASSWORD="your-password"
export SNOWFLAKE_WAREHOUSE="HORNET_QUERY_WH"
export SNOWFLAKE_DATABASE="USER_DB_HORNET"
export SNOWFLAKE_ROLE="TRAINING_ROLE"
export SNOWFLAKE_SCHEMA="ANALYTICS"
```

Or add them to your `~/.zshrc` or `~/.bash_profile`:

```bash
echo 'export SNOWFLAKE_ACCOUNT="your-account.us-west-2"' >> ~/.zshrc
echo 'export SNOWFLAKE_USER="your-username"' >> ~/.zshrc
# ... etc
source ~/.zshrc
```

### 4. Verify Configuration

Check that `config.yaml` exists and has the correct warehouse type:

```bash
cat config.yaml | grep "type:"
# Should show: type: 'snowflake'
```

### 5. Start the System

Run the master start script:

```bash
chmod +x start_all.sh stop_all.sh start_local.sh
./start_all.sh
```

This script will:
1. Check Docker is running
2. Start Docker services (Kafka, Zookeeper, Airflow)
3. Create Python virtual environment (if needed)
4. Install Python dependencies (if needed)
5. Start Backend API
6. Install Node.js dependencies (if needed)
7. Start Frontend

**First run will take 5-10 minutes** as it installs dependencies.

### 6. Verify Services Are Running

After the script completes, verify all services:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin`

### 7. Initial Data Load

1. Open Airflow UI: http://localhost:8080
2. Find `gtfs_incremental_ingestion` DAG
3. Click "Trigger DAG" (play button)
4. Wait for completion (~5-10 minutes)
5. Trigger `transit_streaming` DAG for real-time data
6. Run dbt models:
   ```bash
   cd dbt/transit_dbt
   dbt run --target snowflake
   ```
7. Trigger `ml_forecast_dag` for ML forecasts

## Alternative Setup (Without AWS Secrets Manager)

If you don't have AWS Secrets Manager access, you can use a local `secrets.yaml` file:

### 1. Create secrets.yaml

```bash
cat > secrets.yaml << 'EOF'
snowflake:
  account: "your-account.us-west-2"
  user: "your-username"
  password: "your-password"
  warehouse: "HORNET_QUERY_WH"
  database: "USER_DB_HORNET"
  role: "TRAINING_ROLE"

perplexity:
  api_key: "your-perplexity-api-key"
EOF
```

**Important**: This file is in `.gitignore` and will NOT be committed to the repository.

### 2. Modify Backend to Use Local Secrets

The backend should automatically detect `secrets.yaml` if AWS Secrets Manager is not available. If not, you may need to modify `config/warehouse_config.py` to prioritize local secrets.

## Troubleshooting

### Docker Not Running

```bash
# Start Docker Desktop application
# Or check status:
docker info
```

### Port Already in Use

If ports 3000, 8000, or 8080 are already in use:

1. Find the process:
   ```bash
   lsof -i :3000
   lsof -i :8000
   lsof -i :8080
   ```

2. Kill the process or change ports in:
   - Frontend: `ui/vite.config.ts`
   - Backend: `api/main.py` or use `--port` flag
   - Airflow: `docker-compose.local.yml`

### Python Virtual Environment Issues

```bash
# Remove and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r api/requirements.txt
```

### Node Modules Issues

```bash
cd ui
rm -rf node_modules package-lock.json
npm install
```

### AWS Credentials Not Found

```bash
# Check AWS profile
aws configure list --profile transit-system

# Or set AWS_PROFILE environment variable
export AWS_PROFILE=transit-system
```

### Snowflake Connection Errors

1. Verify credentials in AWS Secrets Manager:
   ```bash
   aws secretsmanager get-secret-value --secret-id transit/snowflake-dev --profile transit-system
   ```

2. Test connection manually:
   ```python
   from api.warehouse_connection import get_warehouse_connection
   with get_warehouse_connection() as conn:
       cursor = conn.cursor()
       cursor.execute("SELECT CURRENT_VERSION()")
       print(cursor.fetchone())
   ```

### Airflow DAGs Not Showing

1. Check Airflow logs:
   ```bash
   docker-compose -f docker-compose.local.yml --profile local logs airflow-webserver
   ```

2. Restart Airflow:
   ```bash
   docker-compose -f docker-compose.local.yml --profile local restart airflow-webserver
   ```

### Kafka Not Starting

```bash
# Check Kafka logs
docker-compose -f docker-compose.local.yml logs kafka

# Restart Kafka
docker-compose -f docker-compose.local.yml restart kafka zookeeper
```

## File Structure

After setup, your directory should look like:

```
transit-system/
├── api/                    # Backend API
├── ui/                     # Frontend
├── airflow/                # Airflow DAGs
├── dbt/                    # dbt models
├── ingestion/              # Data ingestion scripts
├── config/                 # Configuration files
├── scripts/                # Utility scripts
├── config.yaml            # Main config (committed)
├── secrets.yaml           # Local secrets (NOT committed)
├── start_all.sh           # Master start script
├── stop_all.sh            # Master stop script
├── start_local.sh         # Docker services only
├── README.md              # Main documentation
└── SETUP.md               # This file
```

## Next Steps

After successful setup:

1. **Load Initial Data**: Run GTFS ingestion DAG in Airflow
2. **Start Streaming**: Trigger streaming DAG for real-time data
3. **Run dbt Models**: Transform data using dbt
4. **Generate Forecasts**: Run ML forecast DAG
5. **Explore Dashboard**: Open http://localhost:3000

## Stopping Services

To stop all services:

```bash
./stop_all.sh
```

Or manually:

```bash
# Stop backend and frontend
kill $(cat .backend.pid) 2>/dev/null
kill $(cat .frontend.pid) 2>/dev/null

# Stop Docker services
docker-compose -f docker-compose.local.yml --profile local down
```

## Getting Help

If you encounter issues:

1. Check logs:
   - Backend: `tail -f logs/backend.log`
   - Frontend: `tail -f logs/frontend.log`
   - Airflow: `docker-compose -f docker-compose.local.yml --profile local logs -f`

2. Review README.md for detailed component information

3. Check troubleshooting section in README.md

## Notes

- All scripts use relative paths and should work on any Mac
- The system is designed to work with Snowflake (not Redshift in current setup)
- AWS Secrets Manager is the preferred method for credentials
- Local `secrets.yaml` is a fallback option
- All sensitive files are in `.gitignore` and won't be committed

---

**Last Updated**: December 2025
**Tested On**: macOS (all versions with Docker Desktop)

