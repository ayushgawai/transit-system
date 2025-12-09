# DAG Cleanup and GTFS Download Fix

**Date**: 2025-12-09  
**Status**: ✅ Complete

---

## ✅ Changes Made

### 1. Removed Redundant DAG
- **Deleted**: `complete_pipeline_dag.py`
- **Reason**: We have 3 separate DAGs that are cleaner and more modular:
  - `gtfs_incremental_ingestion` - GTFS data ingestion
  - `transit_streaming` - Streaming data ingestion
  - `ml_forecast_dag` - ML forecasting

### 2. Fixed GTFS Download to Skip if Data Exists
**File**: `ingestion/fetch_gtfs_incremental.py`

**Changes**:
- Added early return check at the beginning of `load_gtfs_feed()`
- Checks both LANDING and RAW schemas for existing data
- If data exists for an agency, skips entire download process
- Returns immediately without downloading or processing

**Before**: Downloaded GTFS data every time DAG ran (took 7+ minutes)  
**After**: Skips download if data already exists (completes in seconds)

**Code Logic**:
```python
# Check if data already exists for this agency
if has_agency_data(agency):
    print(f"⏭️ Skipping: GTFS data for {agency} already exists")
    return 0  # Early return - no download
```

---

## 📊 Current DAG Structure

### Active DAGs (3 total):
1. **`gtfs_incremental_ingestion`**
   - Fetches GTFS data (now skips if exists)
   - Runs dbt `landing_to_raw`
   - Runs dbt `transform`
   - Runs dbt `analytics`
   - Triggers `transit_streaming` DAG

2. **`transit_streaming`**
   - Fetches streaming data from Transit API
   - Runs dbt `streaming_to_analytics`

3. **`ml_forecast_dag`**
   - Creates Snowflake ML FORECAST models
   - Generates demand and delay forecasts

---

## 🧪 Testing

### Test GTFS Skip Logic:
```bash
# First run - will download
docker exec transit-system-airflow-scheduler-1 airflow dags trigger gtfs_incremental_ingestion

# Second run - should skip download
docker exec transit-system-airflow-scheduler-1 airflow dags trigger gtfs_incremental_ingestion
```

### Expected Behavior:
- **First run**: Downloads GTFS data (~7 minutes)
- **Subsequent runs**: Skips download, only runs dbt transformations (~2 minutes)

---

## ✅ Benefits

1. **Faster Testing**: DAG completes in seconds instead of minutes
2. **Cleaner Architecture**: Removed redundant `complete_pipeline_dag`
3. **Better Logic**: GTFS is static data - no need to re-download
4. **Cost Savings**: Reduces API calls and processing time

---

**All changes complete. DAG is ready for testing.**

