# MendAI Chat Feature - Complete Implementation Guide

## Overview

The MendAI chat feature enables medical providers to have AI-powered conversational interactions about patient data. The system uses OpenAI's GPT-4 with biomedical-specific prompts and integrates with Google Healthcare FHIR API for patient context.

## Architecture

```
Frontend (React/TypeScript)
    ↓
Engine Service (FastAPI - Port 8000)
    ↓
Biomedical LLM Service (FastAPI - Port 8003)
    ↓
    ├─→ OpenAI API (GPT-4o-mini/GPT-4)
    └─→ Patient Data Service (Port 8001)
            ↓
        Google Healthcare FHIR API
```

## Features

### ✅ Implemented Features

1. **Real-time Chat Interface**
   - Multi-turn conversations with context preservation
   - Patient-specific context injection
   - Loading states and typing indicators
   - Error handling with helpful messages

2. **Patient Context Integration**
   - Automatic FHIR data retrieval
   - Demographics, conditions, medications, observations
   - Enriched prompts with patient medical history
   - Patient indicator in chat header

3. **Biomedical AI Integration**
   - OpenAI GPT-4o-mini for fast responses
   - Biomedical system prompts for clinical accuracy
   - Temperature control for consistent responses
   - Token management and context window optimization

4. **Conversation Management**
   - Session ID tracking across requests
   - Message history maintained throughout conversation
   - Follow-up question capability
   - Context preserved for natural dialogue flow

5. **Caching System**
   - Patient data cached for 10 minutes (in-memory)
   - AI response caching for identical queries
   - Reduced API calls and improved performance

## File Structure

### Backend Files

```
backend/
├── biomedical_llm/
│   ├── biomedical_llm/
│   │   ├── config/
│   │   │   └── config.py                    # Settings management
│   │   ├── services/
│   │   │   ├── openai_service.py            # OpenAI integration
│   │   │   └── patient_data_client.py       # FHIR data fetching
│   │   ├── routes/
│   │   │   └── chat.py                      # Chat endpoints
│   │   ├── data_models/
│   │   │   └── chat.py                      # Pydantic models
│   │   └── main.py                          # FastAPI app
│   ├── pyproject.toml                        # Dependencies
│   ├── .env                                  # Configuration
│   └── README.md                             # Documentation
│
├── engine/
│   └── engine/
│       └── api/
│           └── v0/
│               └── endpoints/
│                   └── chat.py               # Chat forwarding endpoint
│
└── patient_data/
    └── patient_data/
        └── services/
            └── fhir_service.py               # FHIR data normalization
```

### Frontend Files

```
frontend/
└── src/
    ├── pages/
    │   └── PatientDashboardPage/
    │       ├── PatientDashboardPage.tsx      # Chat UI implementation
    │       └── PatientDashboardPage.css      # Chat styling
    └── services/
        └── api.ts                            # API client
```

## Configuration

### Environment Variables

**Backend (biomedical_llm/.env)**:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# Service URLs (local development)
PATIENT_DATA_URL=http://localhost:8001
```

**Docker Environment** (docker-compose.yml):
```yaml
biomedical_llm:
  environment:
    - PATIENT_DATA_URL=http://patient_data:8001
```

### Frontend Configuration

**frontend/.env**:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## API Endpoints

### 1. Chat Endpoint (POST /api/v0/chat)

**Request**:
```json
{
  "messages": [
    {
      "id": "1",
      "type": "user",
      "content": "What medications is this patient taking?",
      "timestamp": "2025-01-01T10:00:00Z"
    }
  ],
  "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "session_id": "generated-or-existing-session-id",
  "messages": [
    {
      "id": "1",
      "type": "user",
      "content": "What medications is this patient taking?",
      "timestamp": "2025-01-01T10:00:00Z"
    },
    {
      "id": "2",
      "type": "assistant",
      "content": "Based on the patient's medical records...",
      "timestamp": "2025-01-01T10:00:05Z"
    }
  ],
  "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177"
}
```

### 2. Available Models Endpoint (GET /models)

**Response**:
```json
{
  "models": [
    {
      "id": "gpt-4o-mini",
      "name": "GPT-4o-mini",
      "description": "Fast and efficient OpenAI model"
    },
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "description": "Most capable OpenAI model"
    }
  ],
  "default_model": "gpt-4o-mini"
}
```

## Running the System

### Option 1: Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f biomedical_llm
docker-compose logs -f engine
docker-compose logs -f patient_data

# Stop services
docker-compose down
```

### Option 2: Local Development

**Terminal 1 - Patient Data Service**:
```bash
cd backend/patient_data
poetry install
poetry run uvicorn patient_data.main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Biomedical LLM Service**:
```bash
cd backend/biomedical_llm
poetry install --without ml  # Skip heavy ML dependencies
poetry run uvicorn biomedical_llm.main:app --host 0.0.0.0 --port 8003 --reload
```

**Terminal 3 - Engine Service**:
```bash
cd backend/engine
poetry install
poetry run uvicorn engine.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 4 - Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## Testing the Chat Feature

### 1. Access the Frontend
Open browser: http://localhost:5173

### 2. Select a Patient
- Navigate to Patient List
- Click on any patient (e.g., Sarah Johnson)
- Go to the "Chat" tab

### 3. Test Queries

**Basic Query**:
```
What medications is this patient currently taking?
```

**Follow-up Question**:
```
Are there any potential interactions between these medications?
```

**Clinical Recommendation**:
```
Based on the patient's conditions, what additional tests would you recommend?
```

**Complex Analysis**:
```
Can you provide a summary of the patient's cardiovascular health based on their observations?
```

### 4. Verify Backend Logs

**Check biomedical_llm logs**:
```bash
# Docker
docker-compose logs -f biomedical_llm

# Local
# Check Terminal 2
```

Look for:
- `Patient data enrichment: Retrieved normalized data for patient...`
- `Chat request received with patient_id...`
- `OpenAI API call successful`

## Troubleshooting

### Issue: "Cannot connect to AI service"

**Symptoms**:
- Error message: "Cannot connect to AI service at http://biomedical_llm:8003"

**Solution**:
```bash
# Check if biomedical_llm service is running
curl http://localhost:8003/health

# Restart the service
docker-compose restart biomedical_llm

# For local development, check Terminal 2
```

### Issue: "No patient data available"

**Symptoms**:
- Chat works but no patient context is included

**Possible Causes**:
1. Patient ID is invalid
2. Patient Data Service is down
3. FHIR data fetch timeout

**Solution**:
```bash
# Test patient data endpoint directly
curl http://localhost:8001/api/patients/a40640b3-b1a1-51ba-bf33-10eb05b37177/bundle-normalized

# Check patient_data service logs
docker-compose logs -f patient_data
```

### Issue: "OpenAI API error"

**Symptoms**:
- Error: "OpenAI API key not found" or "Rate limit exceeded"

**Solution**:
```bash
# Verify API key is set
cd backend/biomedical_llm
cat .env | grep OPENAI_API_KEY

# Update .env file
echo "OPENAI_API_KEY=your_actual_key_here" >> .env

# Restart service
docker-compose restart biomedical_llm
```

### Issue: Frontend shows mock responses

**Symptoms**:
- Chat responses don't include real patient data
- Generic fallback messages

**Solution**:
```bash
# Check browser console (F12) for errors
# Verify API endpoints are accessible
curl http://localhost:8000/health
curl http://localhost:8003/health
curl http://localhost:8001/health

# Check CORS issues - should see headers in response:
curl -I http://localhost:8000/api/v0/chat
```

## Performance Optimization

### 1. Caching Strategy

- **Patient Data Cache**: 10 minutes TTL (in-memory)
- **AI Response Cache**: 10 minutes TTL for identical queries
- **Cache Key Format**: `{patient_id}:{query_hash}`

### 2. Token Management

- **System Prompt**: ~300 tokens
- **Patient Context**: ~500-1000 tokens (varies by patient data)
- **Conversation History**: Limited to last 10 messages
- **Max Response**: 2000 tokens
- **Total Context Window**: ~8000 tokens (GPT-4o-mini)

### 3. Timeout Configuration

- **Frontend → Engine**: 30 seconds
- **Engine → Biomedical LLM**: 60 seconds
- **Biomedical LLM → OpenAI**: 30 seconds
- **Biomedical LLM → Patient Data**: 10 seconds

## Security Considerations

### 1. API Key Protection

- Never commit `.env` files to git
- Use environment variables in production
- Rotate API keys regularly

### 2. Patient Data Privacy

- All patient data uses FHIR IDs (not real identifiers)
- No PII is logged
- HTTPS required in production

### 3. Rate Limiting

- Implement rate limiting on chat endpoint
- Monitor OpenAI API usage
- Set up billing alerts

## Future Enhancements

### Planned Features

1. **Conversation History Persistence**
   - Store chat sessions in database
   - Retrieve previous conversations
   - Export chat transcripts

2. **Multi-modal Input**
   - CT scan image analysis in chat
   - Lab result interpretation
   - Document upload and analysis

3. **Advanced Features**
   - Real-time streaming responses
   - Voice input/output
   - Multi-language support

4. **Analytics**
   - Chat usage metrics
   - Common query patterns
   - Response quality monitoring

## Support and Contact

For issues or questions:
- Check logs in respective services
- Review this documentation
- Verify all services are running
- Check OpenAI API status: https://status.openai.com

## Version History

- **v1.0** (Current): Initial implementation with OpenAI GPT-4o-mini, patient context, conversation history

## License

Proprietary - MendAI Project
