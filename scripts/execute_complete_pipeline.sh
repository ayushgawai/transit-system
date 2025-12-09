#!/bin/bash
# Complete Pipeline Execution Script
# Runs all steps in sequence

set -e  # Exit on error

echo "======================================================================"
echo "COMPLETE PIPELINE EXECUTION"
echo "======================================================================"
echo ""

# Step 1: Create Schemas
echo "Step 1: Creating schemas..."
python3 scripts/create_schemas.py
if [ $? -eq 0 ]; then
    echo "✅ Schemas created"
else
    echo "⚠️  Schema creation had issues (may already exist)"
fi
echo ""

# Step 2: Verify Backend is Running
echo "Step 2: Checking backend..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend not running. Start with: cd api && uvicorn main:app --reload"
    echo "   Continuing with other tests..."
fi
echo ""

# Step 3: Verify Tables
echo "Step 3: Verifying tables..."
python3 scripts/verify_tables.py
echo ""

# Step 4: Test API Endpoints (if backend running)
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "Step 4: Testing API endpoints..."
    python3 scripts/test_all_endpoints.py
    echo ""
    
    echo "Step 5: Testing LLM chat..."
    python3 scripts/test_llm.py
    echo ""
else
    echo "⚠️  Skipping API and LLM tests (backend not running)"
    echo ""
fi

echo "======================================================================"
echo "PIPELINE EXECUTION COMPLETE"
echo "======================================================================"
echo ""
echo "NEXT STEPS:"
echo "  1. Trigger 'gtfs_incremental_ingestion' DAG in Airflow"
echo "  2. Trigger 'ml_forecast_dag' DAG in Airflow"
echo "  3. Review test results above"
echo ""

