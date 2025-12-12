#!/bin/bash
# Master Start Script for Transit System
# Starts all services: Docker (Kafka + Airflow), Backend API, and Frontend
# Usage: ./start_all.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🚀 Transit System - Master Start Script"
echo "============================================================"
echo ""

# Check if Docker is running
echo -e "${BLUE}📦 Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Step 1: Start Docker services (Kafka + Airflow)
echo "============================================================"
echo -e "${BLUE}Step 1/3: Starting Docker Services (Kafka + Airflow)${NC}"
echo "============================================================"
echo ""

echo -e "${YELLOW}📦 Starting Kafka and Zookeeper...${NC}"
docker-compose -f docker-compose.local.yml up -d zookeeper kafka

# Wait for Kafka to be ready
echo -e "${YELLOW}⏳ Waiting for Kafka to be ready...${NC}"
sleep 10

# Check if Kafka is ready
for i in {1..30}; do
    if docker-compose -f docker-compose.local.yml exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Kafka is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Kafka failed to start after 60 seconds${NC}"
        exit 1
    fi
    sleep 2
done

echo -e "${YELLOW}📦 Starting Airflow (PostgreSQL + Webserver + Scheduler)...${NC}"
docker-compose -f docker-compose.local.yml --profile local up -d

echo -e "${GREEN}✅ Docker services started${NC}"
echo ""

# Step 2: Start Backend API
echo "============================================================"
echo -e "${BLUE}Step 2/3: Starting Backend API${NC}"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if API dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing API dependencies...${NC}"
    pip install -r api/requirements.txt > /dev/null 2>&1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start backend in background
echo -e "${YELLOW}🚀 Starting Backend API server...${NC}"
cd api
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo $BACKEND_PID > .backend.pid
echo -e "${GREEN}✅ Backend API started (PID: $BACKEND_PID)${NC}"
echo "   Logs: logs/backend.log"
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Step 3: Start Frontend
echo "============================================================"
echo -e "${BLUE}Step 3/3: Starting Frontend${NC}"
echo "============================================================"
echo ""

# Check if node_modules exists
if [ ! -d "ui/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd ui
    npm install > /dev/null 2>&1
    cd ..
fi

# Start frontend in background
echo -e "${YELLOW}🚀 Starting Frontend development server...${NC}"
cd ui
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo $FRONTEND_PID > .frontend.pid
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "   Logs: logs/frontend.log"
echo "   URL: http://localhost:3000"
echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}✅ All Services Started Successfully!${NC}"
echo "============================================================"
echo ""
echo "Services:"
echo -e "  ${GREEN}✓${NC} Kafka: localhost:9092"
echo -e "  ${GREEN}✓${NC} Zookeeper: localhost:2181"
echo -e "  ${GREEN}✓${NC} Airflow UI: http://localhost:8080"
echo "     Username: admin"
echo "     Password: admin"
echo -e "  ${GREEN}✓${NC} Backend API: http://localhost:8000"
echo "     API Docs: http://localhost:8000/docs"
echo -e "  ${GREEN}✓${NC} Frontend: http://localhost:3000"
echo ""
echo "Process IDs saved to:"
echo "  - .backend.pid"
echo "  - .frontend.pid"
echo ""
echo "To stop all services:"
echo "  ./stop_all.sh"
echo ""
echo "To view logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo "  docker-compose -f docker-compose.local.yml --profile local logs -f"
echo ""
echo -e "${YELLOW}⏳ Waiting 10 seconds for services to initialize...${NC}"
sleep 10
echo ""
echo -e "${GREEN}🎉 Ready! Open http://localhost:3000 in your browser${NC}"
echo ""

