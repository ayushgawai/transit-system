#!/bin/bash
# Master Stop Script for Transit System
# Stops all services: Backend API, Frontend, and Docker services
# Usage: ./stop_all.sh

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
echo "🛑 Transit System - Master Stop Script"
echo "============================================================"
echo ""

# Stop Backend API
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Stopping Backend API (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend.pid
        echo -e "${GREEN}✅ Backend API stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend API process not found${NC}"
        rm .backend.pid
    fi
else
    echo -e "${YELLOW}⚠️  Backend PID file not found${NC}"
fi
echo ""

# Stop Frontend
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Stopping Frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend.pid
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend process not found${NC}"
        rm .frontend.pid
    fi
else
    echo -e "${YELLOW}⚠️  Frontend PID file not found${NC}"
fi
echo ""

# Stop Docker services
echo -e "${YELLOW}🛑 Stopping Docker services (Airflow + Kafka)...${NC}"
docker-compose -f docker-compose.local.yml --profile local down
echo -e "${GREEN}✅ Docker services stopped${NC}"
echo ""

echo "============================================================"
echo -e "${GREEN}✅ All Services Stopped${NC}"
echo "============================================================"
echo ""

