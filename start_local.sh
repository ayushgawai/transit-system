#!/bin/bash
# Start Local Transit System
# Starts Kafka, Airflow, and other local services

set -e

echo "=" | head -c 70
echo ""
echo "🚀 Starting Local Transit System"
echo "=" | head -c 70
echo ""
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Kafka and Zookeeper
echo "📦 Starting Kafka and Zookeeper..."
docker-compose -f docker-compose.local.yml up -d zookeeper kafka

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
sleep 10

# Check if Kafka is ready
for i in {1..30}; do
    if docker-compose -f docker-compose.local.yml exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        echo "✅ Kafka is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Kafka failed to start"
        exit 1
    fi
    sleep 2
done

# Start Airflow
echo "📦 Starting Airflow..."
docker-compose -f docker-compose.local.yml --profile local up -d

echo ""
echo "=" | head -c 70
echo ""
echo "✅ Local Transit System Started"
echo "=" | head -c 70
echo ""
echo "Services:"
echo "  - Kafka: localhost:9092"
echo "  - Airflow UI: http://localhost:8080"
echo "  - Airflow Username: admin"
echo "  - Airflow Password: admin"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.local.yml --profile local down"
echo ""

