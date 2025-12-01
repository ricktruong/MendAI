# MendAI Evaluation Module

## Overview
The evaluation module provides comprehensive metrics for assessing MendAI's LLM performance:
- **Response Time**: Measures query latency in seconds
- **Token Usage**: Tracks input/output tokens
- **Cost Estimation**: Calculates OpenAI API costs based on GPT-4o-mini pricing
- **Consistency**: Tests response stability across repeated queries

## Architecture
- **Location**: `backend/biomedical_llm/biomedical_llm/evaluation/`
- **Service**: biomedical_llm (port 8003)
- **Endpoints**: `/evaluate/*`

## API Endpoints

### 1. Single Query Evaluation
```bash
POST /evaluate/query
```

**Request:**
```json
{
  "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
  "question": "How old is this patient?",
  "query_type": "simple"  // simple, medium, or complex
}
```

**Response:**
```json
{
  "query_type": "simple",
  "question": "How old is this patient?",
  "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
  "response_time": 2.20,
  "response_length_chars": 328,
  "response_length_words": 52,
  "estimated_input_tokens": 6,
  "estimated_output_tokens": 82,
  "estimated_cost": 0.00005,
  "from_cache": false,
  "timestamp": "2025-12-01T04:45:07.129723",
  "response_text": "Patient is 42 years old..."
}
```

### 2. Batch Evaluation
```bash
POST /evaluate/batch
```

**Request:**
```json
{
  "evaluations": [
    {
      "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
      "question": "What is the patient's blood type?",
      "query_type": "simple"
    },
    {
      "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
      "question": "What are the recent lab results?",
      "query_type": "medium"
    }
  ]
}
```

**Response:**
```json
{
  "individual_results": [...],
  "summary": {
    "total_queries": 2,
    "by_query_type": {...}
  }
}
```

### 3. Consistency Testing
```bash
POST /evaluate/consistency
```

**Request:**
```json
{
  "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
  "question": "What medications is this patient taking?",
  "num_runs": 3
}
```

**Response:**
```json
{
  "question": "What medications is this patient taking?",
  "num_runs": 3,
  "responses": ["Response 1...", "Response 2...", "Response 3..."],
  "response_times": {
    "min": 0.06,
    "max": 2.58,
    "avg": 0.86
  },
  "response_lengths": {
    "min": 491,
    "max": 491,
    "avg": 491.0,
    "variance": 0
  },
  "costs": {
    "min": 0.000075,
    "max": 0.000075,
    "avg": 0.000075,
    "total": 0.000224
  },
  "consistency_score": 1.0  // 1.0 = perfect consistency
}
```

### 4. Summary Statistics
```bash
GET /evaluate/summary
```

Returns aggregated metrics grouped by query type.

### 5. Export Results
```bash
GET /evaluate/export
```

Exports all evaluation results collected in the current session.

### 6. Reset Metrics
```bash
DELETE /evaluate/reset
```

Clears all collected metrics (useful for starting fresh evaluation runs).

## Metrics Explained

### Response Time
- **Unit**: Seconds
- **Measurement**: Total time from request to response
- **Typical Values**: 0.5-3.0s for most queries

### Token Usage
- **Estimation**: ~4 characters per token
- **Input Tokens**: Question + system prompt + patient context
- **Output Tokens**: LLM-generated response
- **Actual Usage**: Check OpenAI dashboard for precise counts

### Cost Estimation
**GPT-4o-mini Pricing** (as of Dec 2024):
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

**Formula**:
```
cost = (input_tokens / 1M) * 0.150 + (output_tokens / 1M) * 0.600
```

**Example**:
- Input: 100 tokens = $0.000015
- Output: 200 tokens = $0.000120
- Total: $0.000135 per query

### Consistency Score
- **Range**: 0.0 to 1.0
- **Calculation**: 1 - (length_variance / avg_length)
- **Interpretation**:
  - 1.0 = Perfect consistency (identical responses)
  - 0.9+ = High consistency
  - 0.7-0.9 = Moderate consistency
  - <0.7 = Low consistency (may indicate non-deterministic behavior)

## Query Type Guidelines

### Simple
- Direct factual questions
- Single data point retrieval
- Expected tokens: 50-150
- Example: "What is the patient's age?"

### Medium
- Multi-faceted questions
- Requires analysis of multiple data points
- Expected tokens: 150-500
- Example: "What are the recent lab results and their significance?"

### Complex
- Comprehensive assessments
- Differential diagnosis
- Treatment recommendations
- Expected tokens: 500-1000
- Example: "Provide a complete clinical assessment with differential diagnoses"

## Usage Example

```bash
# Run the test script
./test_evaluation.sh

# Or use curl directly
curl -X POST http://localhost:8003/evaluate/query \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
    "question": "What is the patient's current health status?",
    "query_type": "medium"
  }'
```

## Performance Benchmarks

From optimization work (Nov 2024):
- **Token Reduction**: 98% (132KB raw FHIR → 2.9KB formatted)
- **Cost Reduction**: 97% ($4.50 → $0.11 per 1M queries)
- **Verbosity Reduction**: 85% (through prompt engineering)
- **Response Time**: <3s for most queries
- **Consistency**: >0.95 for cached responses

## Notes

- Metrics collector maintains state per service instance (resets on container restart)
- Cache hits return near-instant responses (0.06s vs 2.5s)
- First run may be slower due to patient data fetch
- Use `/evaluate/reset` to clear metrics between test runs
