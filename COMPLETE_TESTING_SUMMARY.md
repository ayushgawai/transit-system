# Complete Testing Summary & Execution Guide

## ✅ All Changes Completed

### 1. Schema Structure
- ✅ Created proper schema separation: LANDING, RAW, STAGING, TRANSFORM, ANALYTICS, ML
- ✅ All ingestion scripts updated to use LANDING schema
- ✅ All dbt models configured for correct schemas
- ✅ All API endpoints updated to use correct schemas
- ✅ LLM chat handler updated with correct schema references

### 2. Snowflake ML FORECAST Implementation
- ✅ Created `ml_forecast_dag.py` with actual `CREATE SNOWFLAKE.ML.FORECAST`
- ✅ Demand forecast model: Predicts future departures
- ✅ Delay forecast model: Predicts future delays
- ✅ Uses `CALL model_name!FORECAST()` for predictions

### 3. LLM Chat Handler Fixed
- ✅ No more same response for all questions
- ✅ Properly executes SQL queries
- ✅ Returns varied, data-driven responses
- ✅ Handles empty data gracefully

### 4. DAGs Updated
- ✅ `gtfs_incremental_dag.py`: Added transform & analytics dbt tasks
- ✅ `streaming_dag.py`: Fixed ML forecast trigger name
- ✅ All dbt models trigger automatically via DAGs (no manual runs needed)

---

## 🧪 Testing Instructions

### Step 1: Create Schemas
```bash
cd /Users/spartan/Documents/MSDA/Project/transit-system
python3 scripts/create_schemas.py
```

**Expected Output**: All 6 schemas created successfully

---

### Step 2: Run GTFS Ingestion DAG
1. Open Airflow UI: http://localhost:8080
2. Find DAG: `gtfs_incremental_ingestion`
3. Trigger DAG manually
4. Wait for completion (should run: fetch_gtfs → dbt_landing_to_raw → dbt_transform → dbt_analytics → trigger_streaming)

**What it does**:
- Fetches GTFS data → `LANDING` schema
- Runs dbt `landing_to_raw` → Creates `RAW.STG_*` tables
- Runs dbt `transform` → Creates `TRANSFORM.ROUTE_DEPARTURES`
- Runs dbt `analytics` → Creates `ANALYTICS.*` tables
- Triggers streaming DAG

---

### Step 3: Verify Tables
```bash
python3 scripts/verify_tables.py
```

**Expected Output**: All tables exist with data counts

---

### Step 4: Start Backend API
```bash
cd api
uvicorn main:app --reload
```

**Keep this running in a separate terminal**

---

### Step 5: Test API Endpoints
```bash
# In a new terminal
cd /Users/spartan/Documents/MSDA/Project/transit-system
python3 scripts/test_all_endpoints.py
```

**Expected Output**: All endpoints return 200 OK

---

### Step 6: Test LLM Chat
```bash
python3 scripts/test_llm.py
```

**Expected Output**: Varied responses for different questions

**Or test manually**:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Which routes have the highest delays?"}'
```

---

### Step 7: Run Complete E2E Test
```bash
python3 scripts/run_complete_test.py
```

**This runs all tests in sequence**

---

### Step 8: Trigger ML Forecast DAG
1. In Airflow UI, find DAG: `ml_forecast_dag`
2. Trigger manually
3. Wait for completion

**What it does**:
- Creates `ML.DEMAND_FORECAST_MODEL` using Snowflake ML
- Creates `ML.DELAY_FORECAST_MODEL` using Snowflake ML
- Generates forecasts and stores in `ML.DEMAND_FORECAST` and `ML.DELAY_FORECAST`

---

## 📊 Table Verification Checklist

### LANDING Schema
- [ ] `LANDING_GTFS_STOPS` - Has data
- [ ] `LANDING_GTFS_ROUTES` - Has data
- [ ] `LANDING_GTFS_TRIPS` - Has data
- [ ] `LANDING_GTFS_STOP_TIMES` - Has data
- [ ] `LANDING_STREAMING_DEPARTURES` - Has data (after streaming runs)
- [ ] `GTFS_LOAD_HISTORY` - Has data

### RAW Schema
- [ ] `STG_GTFS_STOPS` - Has data (after dbt landing_to_raw)
- [ ] `STG_GTFS_ROUTES` - Has data (after dbt landing_to_raw)
- [ ] `STG_GTFS_TRIPS` - Has data (after dbt landing_to_raw)
- [ ] `STG_GTFS_STOP_TIMES` - Has data (after dbt landing_to_raw)
- [ ] `STG_STREAMING_DEPARTURES` - Has data (after dbt streaming_to_analytics)

### TRANSFORM Schema
- [ ] `ROUTE_DEPARTURES` - Has data (after dbt transform)

### ANALYTICS Schema
- [ ] `RELIABILITY_METRICS` - Has data (after dbt analytics)
- [ ] `DEMAND_METRICS` - Has data (after dbt analytics)
- [ ] `CROWDING_METRICS` - Has data (after dbt analytics)
- [ ] `REVENUE_METRICS` - Has data (after dbt analytics)
- [ ] `DECISION_SUPPORT` - Has data (after dbt analytics)
- [ ] `ROUTE_PERFORMANCE` - Has data (after dbt analytics)

### ML Schema
- [ ] `DEMAND_FORECAST` - Has data (after ml_forecast_dag)
- [ ] `DELAY_FORECAST` - Has data (after ml_forecast_dag)

---

## 🔍 API Endpoint Testing

### Test Each Endpoint:

1. **KPIs**: `GET http://localhost:8000/api/kpis?agency=BART`
2. **Routes**: `GET http://localhost:8000/api/routes?agency=VTA`
3. **Stops**: `GET http://localhost:8000/api/stops?agency=BART`
4. **Live Data**: `GET http://localhost:8000/api/live-data`
5. **Route Health**: `GET http://localhost:8000/api/analytics/route-health?agency=BART`
6. **Route Comparison**: `GET http://localhost:8000/api/analytics/route-comparison`
7. **Delay Analysis**: `GET http://localhost:8000/api/analytics/delay-analysis`
8. **Hourly Demand**: `GET http://localhost:8000/api/hourly-demand?agency=VTA`
9. **Hourly Heatmap**: `GET http://localhost:8000/api/hourly-heatmap`
10. **Demand Forecast**: `GET http://localhost:8000/api/forecasts/demand?hours=6`
11. **Delay Forecast**: `GET http://localhost:8000/api/forecasts/delay`
12. **Admin Status**: `GET http://localhost:8000/api/admin/status`

---

## 💬 LLM Chat Testing

### Test Questions:

1. "Which routes have the highest delays?"
   - **Expected**: List of routes with delay data, not generic response

2. "What's the on-time performance for each route?"
   - **Expected**: Route-by-route on-time percentages

3. "Which routes need attention?"
   - **Expected**: Routes with low performance metrics

4. "What's the average delay for BART?"
   - **Expected**: Specific BART delay statistics

5. "How many routes does VTA have?"
   - **Expected**: Count of VTA routes

6. "Show me route utilization"
   - **Expected**: Utilization metrics by route

7. "What's the reliability score?"
   - **Expected**: Reliability scores from data

**All should return DIFFERENT responses based on actual data**

---

## 🚀 DAG Execution Flow

### Complete Pipeline:
```
gtfs_incremental_ingestion (triggered manually or scheduled)
  ↓
  1. fetch_gtfs_data → LANDING schema
  ↓
  2. dbt_landing_to_raw → RAW schema (STG_* tables)
  ↓
  3. dbt_transform → TRANSFORM schema
  ↓
  4. dbt_analytics → ANALYTICS schema
  ↓
  5. trigger_streaming → transit_streaming DAG
      ↓
      a. kafka_producer → Fetch streaming data
      ↓
      b. kafka_consumer → LANDING.LANDING_STREAMING_DEPARTURES
      ↓
      c. dbt_streaming_to_analytics → RAW.STG_STREAMING_DEPARTURES
      ↓
      d. trigger_ml_forecast → ml_forecast_dag
          ↓
          i. create_demand_forecast_model → ML.DEMAND_FORECAST
          ↓
          ii. create_delay_forecast_model → ML.DELAY_FORECAST
```

**All dbt models run automatically via DAGs - no manual execution needed!**

---

## 📋 Data Cleanup (Without Losing Data)

### Safe Cleanup Steps:

1. **Backup existing tables** (if needed):
   ```sql
   CREATE SCHEMA IF NOT EXISTS BACKUP_20250108;
   CREATE TABLE BACKUP_20250108.LANDING_GTFS_STOPS AS SELECT * FROM ANALYTICS.LANDING_GTFS_STOPS;
   -- Repeat for other tables
   ```

2. **Drop empty/unused tables** (verify first):
   ```sql
   -- Check if table is empty
   SELECT COUNT(*) FROM <schema>.<table>;
   
   -- If empty and not needed, drop it
   DROP TABLE IF EXISTS <schema>.<table>;
   ```

3. **Clean up old forecasts** (keep recent):
   ```sql
   DELETE FROM ML.DEMAND_FORECAST 
   WHERE FORECAST_GENERATED_AT < DATEADD(day, -30, CURRENT_TIMESTAMP());
   
   DELETE FROM ML.DELAY_FORECAST 
   WHERE FORECAST_GENERATED_AT < DATEADD(day, -30, CURRENT_TIMESTAMP());
   ```

---

## 📄 Tableau Dashboard Reference

**See**: `TABLEAU_DASHBOARD_TABLES.md` for complete table reference

**Key Tables for Tableau**:
- `ANALYTICS.RELIABILITY_METRICS` - Main reliability dashboard
- `ANALYTICS.ROUTE_PERFORMANCE` - Route performance dashboard
- `ML.DEMAND_FORECAST` - Forecasting dashboard
- `ML.DELAY_FORECAST` - Delay prediction dashboard
- `RAW.STG_STREAMING_DEPARTURES` - Real-time dashboard

---

## ✅ Final Checklist

- [ ] All schemas created
- [ ] GTFS DAG runs successfully
- [ ] All dbt models run automatically
- [ ] Streaming DAG runs successfully
- [ ] ML Forecast DAG runs successfully
- [ ] All tables have data
- [ ] All API endpoints work
- [ ] LLM chat returns varied responses
- [ ] Tableau documentation ready

---

## 🐛 Troubleshooting

### If DAGs fail:
1. Check Airflow logs for specific errors
2. Verify Snowflake connection in Airflow
3. Check dbt profiles configuration
4. Verify all scripts are accessible in Airflow container

### If API endpoints fail:
1. Check backend is running: `curl http://localhost:8000/docs`
2. Verify Snowflake connection in backend
3. Check schema names match (RAW, ANALYTICS, ML, LANDING)

### If LLM returns same response:
1. Check SQL execution in logs
2. Verify Snowflake connection
3. Check if data exists in tables
4. Review `api/llm/chat_handler.py` logs

### If tables are empty:
1. Run GTFS DAG first
2. Wait for dbt models to complete
3. Check dbt logs for errors
4. Verify data in LANDING schema first

---

**Last Updated**: 2025-01-08
**Status**: ✅ Ready for Testing

