#!/bin/bash

# Test script for MendAI Evaluation Module
# Demonstrates response time, token usage, cost, and consistency metrics

PATIENT_ID="a40640b3-b1a1-51ba-bf33-10eb05b37177"
BASE_URL="http://localhost:8003"

# Create experiment folder with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXPERIMENT_DIR="evaluation_experiments/experiment_${TIMESTAMP}"
mkdir -p "${EXPERIMENT_DIR}"

echo "========================================="
echo "MendAI Evaluation Module Test Script"
echo "========================================="
echo "Experiment folder: ${EXPERIMENT_DIR}"
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

# Test 3: Consistency evaluation (same question, exact wording)
echo "3. Testing consistency with identical wording (3 runs)..."
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

# Test 4: Consistency evaluation with different wording (same question)
echo "4. Testing consistency with different wording (same question)..."
echo "Questions:"
echo "  - Is the patient taking medications?"
echo "  - List the medications they currently have"
echo "  - What medications was the patient prescribed?"
echo ""

# Evaluate each variation
curl -s -X POST ${BASE_URL}/evaluate/query \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"${PATIENT_ID}\",
    \"question\": \"Is the patient taking medications?\",
    \"query_type\": \"consistency_wording_test\"
  }" | python3 -m json.tool > /tmp/med_q1.json

curl -s -X POST ${BASE_URL}/evaluate/query \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"${PATIENT_ID}\",
    \"question\": \"List the medications they currently have\",
    \"query_type\": \"consistency_wording_test\"
  }" | python3 -m json.tool > /tmp/med_q2.json

curl -s -X POST ${BASE_URL}/evaluate/query \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"${PATIENT_ID}\",
    \"question\": \"What medications was the patient prescribed?\",
    \"query_type\": \"consistency_wording_test\"
  }" | python3 -m json.tool > /tmp/med_q3.json

# Display results
echo "Response 1 (Is the patient taking medications?):"
cat /tmp/med_q1.json | jq -r '.response_text' | head -3
echo "..."
echo ""

echo "Response 2 (List the medications they currently have):"
cat /tmp/med_q2.json | jq -r '.response_text' | head -3
echo "..."
echo ""

echo "Response 3 (What medications was the patient prescribed?):"
cat /tmp/med_q3.json | jq -r '.response_text' | head -3
echo "..."
echo ""

# Calculate response length variance
LEN1=$(cat /tmp/med_q1.json | jq -r '.response_length_chars')
LEN2=$(cat /tmp/med_q2.json | jq -r '.response_length_chars')
LEN3=$(cat /tmp/med_q3.json | jq -r '.response_length_chars')

echo "Response lengths: $LEN1, $LEN2, $LEN3 chars"

# Cleanup temp files
rm /tmp/med_q*.json

echo ""
echo "---"
echo ""

# Test 5: Get summary statistics
echo "5. Getting summary statistics from all evaluations..."
curl -s ${BASE_URL}/evaluate/summary | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 6: Export all results
echo "6. Exporting all evaluation results..."
curl -s ${BASE_URL}/evaluate/export | python3 -m json.tool | head -30

echo ""
echo "---"
echo ""

# Save results to files
echo "7. Saving results to experiment folder..."
RESULTS_FILE="${EXPERIMENT_DIR}/results.json"
SUMMARY_FILE="${EXPERIMENT_DIR}/summary.json"

curl -s ${BASE_URL}/evaluate/export | python3 -m json.tool > "${RESULTS_FILE}"
curl -s ${BASE_URL}/evaluate/summary | python3 -m json.tool > "${SUMMARY_FILE}"

# Save experiment metadata
cat > "${EXPERIMENT_DIR}/metadata.json" << EOF
{
  "timestamp": "${TIMESTAMP}",
  "experiment_date": "$(date)",
  "patient_id": "${PATIENT_ID}",
  "base_url": "${BASE_URL}",
  "test_types": ["simple", "medium", "consistency_identical", "consistency_wording"]
}
EOF

echo "Results saved to: ${RESULTS_FILE}"
echo "Summary saved to: ${SUMMARY_FILE}"
echo "Metadata saved to: ${EXPERIMENT_DIR}/metadata.json"

# Also save as latest (for quick access)
cp "${RESULTS_FILE}" "evaluation_results.json"
cp "${SUMMARY_FILE}" "evaluation_summary.json"
echo "Latest results also saved to: evaluation_results.json"
echo "Latest summary also saved to: evaluation_summary.json"

echo ""
echo "========================================="
echo "Evaluation tests complete!"
echo "Experiment saved in: ${EXPERIMENT_DIR}"
echo "========================================="
