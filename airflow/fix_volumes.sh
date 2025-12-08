#!/bin/bash
# Fix Airflow volume mounts by setting PROJECT_ROOT

# Get the project root (parent of airflow directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Setting PROJECT_ROOT to: $PROJECT_ROOT"
export PROJECT_ROOT

# Restart Airflow
cd "$SCRIPT_DIR"
echo "Restarting Airflow..."
docker-compose down
docker-compose up -d

echo ""
echo "✅ Airflow restarted with correct volume mounts!"
echo "Check logs: docker-compose logs -f"

