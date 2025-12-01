#!/bin/bash

# MendAI Chat Feature - Quick Test Script
# This script tests the chat feature end-to-end

echo "================================================"
echo "  MendAI Chat Feature - Integration Test"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
PATIENT_ID="a40640b3-b1a1-51ba-bf33-10eb05b37177"
TEST_MESSAGE="What medications is this patient currently taking?"

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    
    echo -n "Checking $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo -e "${GREEN}✓ Online${NC}"
        return 0
    else
        echo -e "${RED}✗ Offline${NC}"
        return 1
    fi
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=$3
    local data=$4
    
    echo ""
    echo "Testing: $name"
    echo "URL: $url"
    echo ""
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "\n%{http_code}")
        
        status_code=$(echo "$response" | tail -n 1)
        body=$(echo "$response" | head -n -1)
        
        if [ "$status_code" = "200" ]; then
            echo -e "${GREEN}✓ Success (HTTP $status_code)${NC}"
            echo ""
            echo "Response preview:"
            echo "$body" | python3 -m json.tool | head -n 20
            echo "..."
            return 0
        else
            echo -e "${RED}✗ Failed (HTTP $status_code)${NC}"
            echo "Response:"
            echo "$body"
            return 1
        fi
    else
        response=$(curl -s "$url")
        echo "$response" | python3 -m json.tool
    fi
}

echo "Step 1: Health Checks"
echo "---------------------"
check_service "Patient Data Service" "http://localhost:8001/health"
patient_data_ok=$?

check_service "Biomedical LLM Service" "http://localhost:8003/health"
biomedical_llm_ok=$?

check_service "Engine Service" "http://localhost:8000/health"
engine_ok=$?

echo ""

# Check if all services are running
if [ $patient_data_ok -ne 0 ] || [ $biomedical_llm_ok -ne 0 ] || [ $engine_ok -ne 0 ]; then
    echo -e "${RED}ERROR: Not all services are running!${NC}"
    echo ""
    echo "To start services:"
    echo "  Option 1 (Docker): docker-compose up -d"
    echo "  Option 2 (Local): See CHAT_FEATURE_GUIDE.md for manual startup"
    exit 1
fi

echo -e "${GREEN}All services are running!${NC}"
echo ""

echo "Step 2: Test Patient Data Retrieval"
echo "------------------------------------"
test_endpoint \
    "Get Normalized Patient Data" \
    "http://localhost:8001/api/patients/$PATIENT_ID/bundle-normalized" \
    "GET"

echo ""

echo "Step 3: Test Biomedical LLM Models"
echo "-----------------------------------"
test_endpoint \
    "List Available Models" \
    "http://localhost:8003/models" \
    "GET"

echo ""

echo "Step 4: Test Chat Endpoint (End-to-End)"
echo "----------------------------------------"

# Prepare chat request
chat_request=$(cat <<EOF
{
  "messages": [
    {
      "id": "test-1",
      "type": "user",
      "content": "$TEST_MESSAGE",
      "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    }
  ],
  "patient_id": "$PATIENT_ID",
  "session_id": "test-session-$(date +%s)"
}
EOF
)

test_endpoint \
    "Send Chat Message" \
    "http://localhost:8000/api/v0/chat" \
    "POST" \
    "$chat_request"

echo ""
echo "================================================"
echo "  Test Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Open browser: http://localhost:5173"
echo "  2. Navigate to Patient List"
echo "  3. Select a patient"
echo "  4. Go to Chat tab"
echo "  5. Start chatting!"
echo ""
echo -e "${YELLOW}Note: Make sure frontend is running (npm run dev)${NC}"
