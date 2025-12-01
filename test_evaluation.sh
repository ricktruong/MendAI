#!/bin/bash

# Test script for MendAI Evaluation Module
# Demonstrates response time, token usage, cost, and consistency metrics

PATIENT_ID="a40640b3-b1a1-51ba-bf33-10eb05b37177"
BASE_URL="http://localhost:8003"

echo "========================================="
echo "MendAI Evaluation Module Test Script"
echo "========================================="
echo ""

# Test 1: Simple query evaluation
echo "1. Testing simple query evaluation..."
curl -s -X POST ${BASE_URL}/evaluate/query \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"${PATIENT_ID}\",
    \"question\": \"What is the patient's blood type?\",
    \"query_type\": \"simple\"
  }" | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 2: Medium complexity query
echo "2. Testing medium complexity query..."
curl -s -X POST ${BASE_URL}/evaluate/query \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"${PATIENT_ID}\",
    \"question\": \"What are the most recent lab results and what do they indicate?\",
    \"query_type\": \"medium\"
  }" | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 3: Consistency evaluation (3 runs)
echo "3. Testing consistency across 3 identical queries..."
curl -s -X POST ${BASE_URL}/evaluate/consistency \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"${PATIENT_ID}\",
    \"question\": \"Summarize this patient's current health status\",
    \"num_runs\": 3
  }" | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 4: Get summary statistics
echo "4. Getting summary statistics from all evaluations..."
curl -s ${BASE_URL}/evaluate/summary | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 5: Export all results
echo "5. Exporting all evaluation results..."
curl -s ${BASE_URL}/evaluate/export | python3 -m json.tool | head -30

echo ""
echo "========================================="
echo "Evaluation tests complete!"
echo "========================================="
