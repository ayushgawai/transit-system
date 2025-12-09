#!/usr/bin/env python3
"""
Trigger Airflow DAGs programmatically
"""
import requests
import time
import sys

AIRFLOW_URL = "http://localhost:8080"
AIRFLOW_USERNAME = "airflow"
AIRFLOW_PASSWORD = "airflow"

def trigger_dag(dag_id):
    """Trigger a DAG run"""
    url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    auth = (AIRFLOW_USERNAME, AIRFLOW_PASSWORD)
    
    data = {
        "conf": {},
        "dag_run_id": f"manual_{int(time.time())}"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, auth=auth, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully triggered DAG: {dag_id}")
            print(f"   DAG Run ID: {result.get('dag_run_id')}")
            return True
        else:
            print(f"❌ Failed to trigger DAG {dag_id}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error triggering DAG {dag_id}: {e}")
        return False

def check_dag_status(dag_id):
    """Check if DAG exists and is active"""
    url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}"
    auth = (AIRFLOW_USERNAME, AIRFLOW_PASSWORD)
    
    try:
        response = requests.get(url, auth=auth, timeout=10)
        if response.status_code == 200:
            dag_info = response.json()
            is_paused = dag_info.get('is_paused', True)
            if is_paused:
                print(f"⚠️  DAG {dag_id} is paused. Unpausing...")
                # Unpause the DAG
                unpause_url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}"
                unpause_response = requests.patch(
                    unpause_url,
                    json={"is_paused": False},
                    auth=auth,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                if unpause_response.status_code == 200:
                    print(f"✅ DAG {dag_id} unpaused")
                else:
                    print(f"⚠️  Could not unpause DAG {dag_id}")
            return True
        else:
            print(f"❌ DAG {dag_id} not found or not accessible")
            return False
    except Exception as e:
        print(f"❌ Error checking DAG {dag_id}: {e}")
        return False

def main():
    dags_to_trigger = [
        "gtfs_incremental_ingestion",
        "ml_forecast_dag"
    ]
    
    print("=" * 80)
    print("TRIGGERING AIRFLOW DAGS")
    print("=" * 80)
    print()
    
    for dag_id in dags_to_trigger:
        print(f"Checking DAG: {dag_id}")
        if check_dag_status(dag_id):
            print(f"Triggering DAG: {dag_id}")
            trigger_dag(dag_id)
            print()
        else:
            print(f"⚠️  Skipping {dag_id} - not found or not accessible")
            print()
    
    print("=" * 80)
    print("✅ DAG triggering complete")
    print("=" * 80)
    print()
    print("Monitor DAGs at: http://localhost:8080")

if __name__ == "__main__":
    main()

