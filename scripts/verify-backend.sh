#!/bin/bash

echo ""
echo "========================================="
echo "  MendAI Backend Health Check"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Check Docker is running
echo "[1/5] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not installed"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker daemon is not running"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker is running"

# Check Docker Compose
echo ""
echo "[2/5] Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker Compose is not installed"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker Compose is installed"

# Check containers
echo ""
echo "[3/5] Checking Docker containers..."
RUNNING_CONTAINERS=$(docker ps --filter "name=mendai" --format "{{.Names}}")
if [ -z "$RUNNING_CONTAINERS" ]; then
    echo -e "${YELLOW}[WARNING]${NC} No MendAI containers found running"
    echo "Run 'docker-compose up -d' in the backend directory"
else
    echo -e "${GREEN}[OK]${NC} MendAI containers are running:"
    docker ps --filter "name=mendai" --format "table {{.Names}}\t{{.Status}}"
fi

# Check API endpoints
echo ""
echo "[4/5] Checking API endpoints..."
echo ""

# Function to check service health
check_service() {
    local name=$1
    local port=$2
    local url="http://localhost:${port}/health"

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} $name ($port): Running"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name ($port): Not responding"
        FAILED=1
        return 1
    fi
}

# Check all services
check_service "Engine Service" "8000"
check_service "Patient Data Service" "8001"
check_service "Medical Imaging Service" "8002"
check_service "Biomedical LLM Service" "8003"

# Summary
echo ""
echo "[5/5] Summary"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "========================================="
    echo -e "  ${GREEN}All services are healthy!${NC}"
    echo "========================================="
    echo ""
    exit 0
else
    echo "========================================="
    echo -e "  ${RED}Some services are not responding${NC}"
    echo "========================================="
    echo ""
    echo "Please check:"
    echo "1. Docker containers are running: docker ps"
    echo "2. Check container logs: docker-compose logs"
    echo "3. Restart services: docker-compose restart"
    echo ""
    exit 1
fi
