# MendAI: A Multimodal AI Assistant for Smarter Clinical Decision-Making

MendAI, your agentic AI healthcare assistant, seamlessly integrates with your hospital's EHR system, patients' data, medical scans, laboratory results, and clinical text, to give to healthcare professionals like you AI-assisted patient prognosis all within one seamless, integrated medical workflow solution.

## 🎯 Key Features

### 🧠 Intelligent Conversation Memory
- **Persistent Chat History**: AI remembers your entire conversation with each patient
- **Auto-Restoration**: Conversations persist across page refreshes and navigation
- **Smart Context Management**: Token-aware context window (max 2000 tokens)
- **Session Isolation**: Separate conversation history for each patient
- **User Controls**: Clear conversation button with confirmation dialog
- **24-Hour Session TTL**: Automatic cleanup of expired sessions

### ⚡ High-Performance Pagination
- **Fast Initial Load**: Only 20 patients loaded by default (vs 100 previously)
- **Flexible Page Sizes**: Choose 10, 20, 50, or 100 patients per page
- **Rich Navigation**: First/Previous/Next/Last buttons with page numbers
- **Smart Page Range**: Displays 5 page numbers with intelligent positioning
- **Performance**: 80% reduction in initial page load time (1-2s vs 5-10s)

### 🏥 Patient Data Management
- **FHIR Integration**: Google Healthcare API for standardized patient data
- **Comprehensive Search**: Search across all patient fields
- **Bulk Operations**: Add, edit, and delete patient records
- **File Management**: Upload and manage patient files and attachments
- **Age Calculation**: Corrected FHIR date handling with proper age display

### 🔬 Medical Imaging Analysis
- **DICOM Processing**: CT scan analysis with AI-powered insights
- **Batch Analysis**: Process multiple images simultaneously
- **Base64 Support**: Direct image display in the frontend
- **Slice-Based Analysis**: Detailed examination of scan slices

### 🤖 AI-Powered Clinical Assistant
- **GPT-4o-mini Integration**: Advanced OpenAI model for medical queries
- **Clinical Context**: Dan's specialized clinical prompt for accurate responses
- **Real-Time Chat**: Instant responses to medical questions
- **Patient-Specific Context**: AI receives full patient FHIR data for contextual answers

## 🏗️ Architecture

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│         React Frontend (Vite, TypeScript)               │
│  • Patient List with Pagination                         │
│  • Patient Dashboard with Chat                          │
│  • Conversation Memory (localStorage)                   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│       Backend Engine (FastAPI) - Port 8000              │
│  • API Gateway & Routing                                │
│  • Conversation Manager (Session Storage)               │
│  • Pagination Logic                                     │
│  • Health Monitoring                                    │
└───┬─────────────┬─────────────────┬──────────────────┬──┘
    │             │                 │                  │
    ▼             ▼                 ▼                  ▼
┌─────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Patient  │ │Medical       │ │Biomedical    │ │Conversation  │
│Data     │ │Imaging       │ │LLM           │ │Manager       │
│Service  │ │Service       │ │Service       │ │(In-Memory)   │
│         │ │              │ │              │ │              │
│Port 8001│ │Port 8002     │ │Port 8003     │ │Max 2000      │
│         │ │              │ │              │ │tokens        │
│FHIR API │ │DICOM/MONAI   │ │GPT-4o-mini   │ │24hr TTL      │
└─────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Key Components:**
- **Frontend**: React 18 + TypeScript + Vite for fast, type-safe UI
- **API Gateway**: FastAPI engine orchestrating all backend services
- **Conversation Manager**: Session-based memory with intelligent context management
- **Patient Data**: FHIR-compliant patient information with pagination
- **Medical Imaging**: AI-powered scan analysis with MONAI framework
- **Biomedical LLM**: OpenAI GPT-4o-mini with clinical prompt engineering

## 📁 Project Structure

```
Project/
├── frontend/                # React + Vite + TypeScript
│   ├── src/                 # Source code
│   ├── Dockerfile           # Frontend container
│   └── nginx.conf           # Nginx configuration
├── backend/
│   ├── engine/              # Main backend engine (API gateway, routing)
│   ├── patient_data/        # Patient data service (Epic FHIR integration)
│   ├── medical_imaging/     # Medical imaging service (MONAI)
│   ├── biomedical_llm/      # LLM service (MONAI + Transformers)
│   └── common/              # Shared code and utilities
├── docker-compose.yml       # Complete application orchestration
├── Makefile                 # Management commands
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

**Required:**
- **Docker Desktop** (v20.10+) - [Download here](https://www.docker.com/products/docker-desktop)
- **Docker Compose** (v2.0+) - Included with Docker Desktop
- **Git** - For cloning the repository

**Optional (for local development):**
- **Python 3.9+** - Backend development
- **Node.js 18+** - Frontend development
- **Poetry** - Python dependency management: `curl -sSL https://install.python-poetry.org | python3 -`

**Environment Setup:**
- **OpenAI API Key** - Required for LLM functionality
- **Google Cloud Credentials** - Required for FHIR data access

### Option 1: Docker (Recommended for Production)

#### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/ricktruong/MendAI.git
cd MendAI

# Run automated setup script
chmod +x setup.sh
./setup.sh
```

**What the setup script does:**
- ✅ Checks all prerequisites (Docker, Node.js, Python, Poetry)
- ✅ Fixes common Docker issues and cleans build cache
- ✅ Creates environment files for all services
- ✅ Installs backend dependencies (Poetry)
- ✅ Installs frontend dependencies (npm)
- ✅ Validates project structure
- ✅ Optionally tests Docker builds

#### 2. Configure Environment Variables

Edit the generated environment files with your credentials:

```bash
# Backend Engine - OpenAI API Key required
nano backend/engine/.env

# Add your OpenAI API key:
OPENAI_API_KEY=sk-your-api-key-here

# Patient Data Service - Google Cloud credentials required
nano backend/patient_data/.env

# Set your Google Cloud project and credentials path:
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

#### 3. Start All Services

```bash
# Build and start all services
make build
make up

# Or combine in one command:
make build up

# View logs to verify all services started correctly
make logs
```

#### 4. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Patient Data API**: http://localhost:8001/docs
- **Biomedical LLM API**: http://localhost:8003/docs

#### 5. Verify Service Health

```bash
# Check all service health endpoints
make health

# Or manually:
curl http://localhost:8000/health  # Engine
curl http://localhost:8001/health  # Patient Data
curl http://localhost:8003/health  # Biomedical LLM
curl http://localhost:3000/        # Frontend
```

#### Management Commands

```bash
make help          # Show all available commands
make build         # Build all Docker images
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make logs          # View logs from all services
make logs-engine   # View engine service logs
make logs-frontend # View frontend logs
make status        # Check service status
make health        # Check service health endpoints
make clean         # Remove containers and volumes
```

**GPU Support (Optional - for AI/ML acceleration):**

If you have an NVIDIA GPU and want to accelerate AI processing:

```bash
# Install NVIDIA Docker Runtime first:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# Build and run with GPU support
make gpu-build
make gpu-up
```

### Option 2: Local Development (Recommended for Development)

Perfect for active development with hot-reload capabilities.

#### 1. Clone and Setup

```bash
git clone https://github.com/ricktruong/MendAI.git
cd MendAI

# Run setup script to prepare environment
./setup.sh
```

#### 2. Configure Environment Variables

Same as Docker setup - edit environment files in each service directory.

#### 3. Start Backend Services

Open **4 separate terminal windows** and run each service:

**Terminal 1 - Patient Data Service:**
```bash
cd backend/patient_data
poetry install
poetry run uvicorn patient_data.main:app --port 8001 --reload
```

**Terminal 2 - Biomedical LLM Service:**
```bash
cd backend/biomedical_llm
poetry install

# Set environment variable for patient data service URL
export PATIENT_DATA_URL=http://localhost:8001

poetry run uvicorn biomedical_llm.main:app --port 8003 --reload
```

**Terminal 3 - Engine Service (Main API Gateway):**
```bash
cd backend/engine
poetry install

# Set environment variables for other services
export PATIENT_DATA_SERVICE_URL=http://localhost:8001
export BIOMEDICAL_LLM_URL=http://localhost:8003

poetry run uvicorn engine.main:app --port 8000 --reload
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

#### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

**Why Local Development?**
- ✅ Instant hot-reload on code changes
- ✅ Better debugging with direct terminal output
- ✅ Faster iteration cycle
- ✅ Direct access to logs and errors
- ✅ No Docker build time

### Quick Test

Once services are running, test the key features:

```bash
# 1. Test patient list with pagination
curl http://localhost:8000/api/v0/dashboard?page=1&page_size=20

# 2. Test conversation memory (requires session_id from chat)
curl http://localhost:8000/api/v0/chat/stats

# 3. Access frontend and try:
#    - Load patient list (should be fast with pagination)
#    - Click a patient to open dashboard
#    - Ask a question in chat
#    - Refresh page (conversation should persist)
#    - Ask follow-up question (AI should remember context)
```

## 🔧 Services & Ports

### Frontend (Port 3000)
- **Technology**: React 18 + TypeScript + Vite
- **Features**:
  - Patient list with pagination controls
  - Patient dashboard with real-time chat
  - Conversation memory with localStorage persistence
  - Responsive design for healthcare workflows
  - Hot module replacement in development

### Backend Engine (Port 8000)
- **Technology**: FastAPI + Python 3.9+
- **Features**:
  - API gateway and request routing
  - Conversation Manager with session storage
  - Pagination endpoint for patient list
  - Health monitoring and status checks
  - Service orchestration
  - Auto-reload in development mode

**Key Endpoints:**
- `GET /api/v0/dashboard?page=1&page_size=20` - Paginated patient list
- `POST /api/v0/chat` - Send chat message with conversation memory
- `GET /api/v0/chat/history/{session_id}` - Retrieve conversation history
- `DELETE /api/v0/chat/history/{session_id}` - Clear conversation
- `GET /api/v0/chat/stats` - System-wide conversation statistics
- `GET /health` - Service health check

### Patient Data Service (Port 8001)
- **Technology**: FastAPI + Google Healthcare FHIR API
- **Features**:
  - FHIR-compliant patient data access
  - Patient record CRUD operations
  - Biometric data management
  - Medical history tracking
  - Corrected age calculation (FHIR date handling)
  - Secure credential management

**Key Endpoints:**
- `GET /api/v0/patients` - List all patients
- `GET /api/v0/patients/{id}` - Get patient details
- `POST /api/v0/patients` - Create new patient
- `PUT /api/v0/patients/{id}` - Update patient
- `DELETE /api/v0/patients/{id}` - Delete patient
- `GET /health` - Service health check

### Medical Imaging Service (Port 8002)
- **Technology**: FastAPI + MONAI + PyTorch
- **Features**:
  - DICOM file processing and conversion
  - CT scan segmentation and analysis
  - Batch image processing
  - Slice-based analysis
  - Base64 image encoding for frontend
  - AI-powered disease detection

**Key Endpoints:**
- `POST /api/v0/imaging/analyze` - Analyze medical images
- `POST /api/v0/imaging/batch` - Batch image processing
- `POST /api/v0/imaging/convert` - DICOM conversion
- `GET /health` - Service health check

### Biomedical LLM Service (Port 8003)
- **Technology**: FastAPI + OpenAI GPT-4o-mini
- **Features**:
  - Medical question answering with Dan's clinical prompt
  - Patient context integration (FHIR data)
  - Real-time chat responses
  - Token-optimized context management
  - Multimodal medical analysis
  - Clinical knowledge base

**Key Endpoints:**
- `POST /api/v0/chat` - Chat with biomedical LLM
- `POST /api/v0/analyze` - Analyze patient case
- `GET /health` - Service health check

**Configuration:**
- Requires `OPENAI_API_KEY` environment variable
- Uses GPT-4o-mini model for cost-effective, fast responses
- Dan's specialized clinical prompt for accurate medical context

## 🛠️ Tech Stack

### Frontend
- **React 18** - Modern UI framework with hooks
- **TypeScript** - Type-safe JavaScript for reliability
- **Vite** - Lightning-fast build tool and dev server
- **Axios** - HTTP client for API calls
- **CSS Modules** - Component-scoped styling
- **localStorage** - Client-side conversation persistence

### Backend Services
- **FastAPI** - High-performance async web framework
- **Python 3.9+** - Modern Python with type hints
- **Poetry** - Dependency management and packaging
- **Uvicorn** - ASGI server with auto-reload
- **Pydantic** - Data validation and settings management
- **httpx** - Async HTTP client for service communication

### AI & Machine Learning
- **OpenAI GPT-4o-mini** - Advanced language model
- **MONAI** - Medical Open Network for AI
- **PyTorch** - Deep learning framework
- **Transformers** - HuggingFace model library
- **NumPy/SciPy** - Scientific computing

### Data & Integration
- **Google Healthcare FHIR API** - Patient data standard
- **DICOM** - Medical imaging standard
- **REST APIs** - Service-to-service communication
- **JSON** - Data interchange format

### Infrastructure & DevOps
- **Docker** - Container platform
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Frontend web server
- **Make** - Build automation
- **Git** - Version control

### Development Tools
- **ESLint** - JavaScript linting
- **Prettier** - Code formatting
- **pytest** - Python testing
- **Black** - Python code formatter

## 📊 New Features Documentation

### 🧠 Conversation Memory System

The conversation memory system allows the AI to remember context across the entire patient session.

**Architecture:**
- **Session Storage**: In-memory dictionary storing conversation history
- **Session ID**: UUID generated per patient, stored in localStorage
- **TTL**: 24-hour automatic session expiration
- **Context Window**: Max 2000 tokens to optimize LLM performance
- **Message Limit**: Up to 50 messages per session

**How It Works:**
1. User opens patient dashboard → Session ID generated or restored from localStorage
2. User asks question → Message stored in ConversationManager before LLM call
3. AI responds → Response stored in ConversationManager
4. User refreshes page → Session ID retrieved from localStorage, history restored
5. User continues conversation → AI has full context of previous messages

**API Endpoints:**
```bash
# Get conversation history
GET /api/v0/chat/history/{session_id}

# Delete conversation (clear history)
DELETE /api/v0/chat/history/{session_id}

# Get conversation statistics
GET /api/v0/chat/stats
```

**Frontend Integration:**
- `PatientDashboardPage.tsx` manages session lifecycle
- localStorage key: `chat_session_${patientId}`
- "Clear Conversation" button with confirmation dialog
- Auto-restoration on component mount

**Configuration:**
```python
# backend/engine/services/conversation_manager.py
MAX_MESSAGES_PER_SESSION = 50
SESSION_TTL_HOURS = 24
MAX_CONTEXT_TOKENS = 2000
```

**Testing:**
See [CONVERSATION_MEMORY_TEST_GUIDE.md](CONVERSATION_MEMORY_TEST_GUIDE.md) for comprehensive testing instructions.

### ⚡ Pagination System

Dramatically improves performance by loading patients in smaller batches.

**Backend Implementation:**
```python
# backend/engine/api/v0/endpoints/dashboard.py
@router.get("/dashboard")
async def get_patient_list_data(
    page: int = 1,           # Current page number
    page_size: int = 20      # Items per page (10/20/50/100)
):
    # Calculate indices
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    
    # Return paginated data
    return {
        "patients": patients[start_idx:end_idx],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size)
    }
```

**Frontend Implementation:**
```typescript
// frontend/src/pages/PatientListPage/PatientListPage.tsx
const [currentPage, setCurrentPage] = useState(1);
const [pageSize, setPageSize] = useState(20);
const [totalPatients, setTotalPatients] = useState(0);
const [totalPages, setTotalPages] = useState(0);

// Load data when page changes
useEffect(() => {
  loadPatientListData();
}, [currentPage, pageSize]);
```

**UI Controls:**
- First/Previous/Next/Last navigation buttons
- Page number buttons (shows 5 at a time)
- Page size selector (10, 20, 50, 100 per page)
- "Showing X to Y of Z patients" info display
- Disabled state during loading
- Smart page range calculation

**Performance Impact:**
- **Before**: 5-10 seconds to load 100 patients
- **After**: 1-2 seconds to load 20 patients
- **Improvement**: 80% faster initial load time

**Configuration:**
```typescript
// Default page sizes available
const PAGE_SIZES = [10, 20, 50, 100];
const DEFAULT_PAGE_SIZE = 20;
```

## 🔍 Monitoring & Health Checks

All services include comprehensive health check endpoints:

```bash
# Check all services at once
make health

# Or check individually:
curl http://localhost:8000/health    # Engine (API Gateway)
curl http://localhost:8001/health    # Patient Data Service
curl http://localhost:8002/health    # Medical Imaging Service
curl http://localhost:8003/health    # Biomedical LLM Service
curl http://localhost:3000/          # Frontend (should return HTML)
```

**Health Check Response:**
```json
{
  "status": "healthy",
  "service": "engine",
  "version": "1.0.0",
  "timestamp": "2025-11-16T12:00:00Z"
}
```

**Service Logs:**
```bash
# View all logs
make logs

# View specific service logs
make logs-engine
make logs-frontend
make logs-patient-data
make logs-llm

# Follow logs in real-time
docker-compose logs -f engine
```

**Conversation Statistics:**
```bash
# Get system-wide conversation stats
curl http://localhost:8000/api/v0/chat/stats

# Response:
{
  "total_sessions": 15,
  "active_sessions": 8,
  "total_messages": 234,
  "avg_messages_per_session": 15.6
}
```

## 🔒 Security & Best Practices

### Environment Variables
**Never commit sensitive data!** All services use environment files:

```bash
# These files are in .gitignore
backend/engine/.env
backend/patient_data/.env
backend/medical_imaging/.env
backend/biomedical_llm/.env
frontend/.env
```

**Required Environment Variables:**

**Backend Engine:**
```bash
OPENAI_API_KEY=sk-your-openai-api-key
PATIENT_DATA_SERVICE_URL=http://localhost:8001
BIOMEDICAL_LLM_URL=http://localhost:8003
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

**Patient Data Service:**
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
SERVICE_PORT=8001
```

**Biomedical LLM Service:**
```bash
OPENAI_API_KEY=sk-your-openai-api-key
PATIENT_DATA_URL=http://localhost:8001
SERVICE_PORT=8003
```

### Container Security
- ✅ Non-root users in all containers
- ✅ Network isolation between services
- ✅ Read-only file systems where possible
- ✅ Minimal base images (Alpine Linux)
- ✅ No hardcoded secrets

### API Security
- ✅ CORS configuration for frontend
- ✅ Request validation with Pydantic
- ✅ Health check endpoints (no auth required)
- ✅ Environment-based configuration
- ⚠️ **Production TODO**: Add JWT authentication

## 🚀 Production Deployment

### Pre-Production Checklist

- [ ] Set `ENVIRONMENT=production` in all `.env` files
- [ ] Set `DEBUG=false` in all `.env` files
- [ ] Generate strong secrets for production
- [ ] Configure proper logging levels (`LOG_LEVEL=WARNING`)
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Review CORS settings
- [ ] Set up CI/CD pipeline

### Docker Production Configuration

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Start with production settings
docker-compose up -d

# Scale services as needed
docker-compose up -d --scale engine=2 --scale llm=2
```

### Environment Configuration

**Production .env example:**
```bash
# backend/engine/.env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
OPENAI_API_KEY=sk-prod-key-here
SECRET_KEY=your-strong-secret-key
JWT_SECRET=your-jwt-secret
ALLOWED_ORIGINS=https://yourdomain.com
```

### Scaling Strategies

**Horizontal Scaling:**
```bash
# Scale specific services
docker-compose up -d --scale engine=3
docker-compose up -d --scale llm=2
```

**Load Balancing:**
- Use Nginx or Traefik for load balancing
- Configure health checks for automatic failover
- Implement sticky sessions for conversation memory

**Database Migration:**
- Currently uses in-memory storage for conversations
- **Production TODO**: Migrate to Redis or PostgreSQL for persistence
- Implement session replication across instances

## 🧪 Testing

### Manual Testing

**Test Pagination:**
```bash
# Test different page sizes
curl "http://localhost:8000/api/v0/dashboard?page=1&page_size=10"
curl "http://localhost:8000/api/v0/dashboard?page=2&page_size=20"
curl "http://localhost:8000/api/v0/dashboard?page=1&page_size=50"
```

**Test Conversation Memory:**
```bash
# 1. Start a conversation (get session_id from response)
curl -X POST http://localhost:8000/api/v0/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the patient'\''s blood pressure?",
    "patient_id": "123",
    "session_id": "test-session-uuid"
  }'

# 2. Get conversation history
curl http://localhost:8000/api/v0/chat/history/test-session-uuid

# 3. Send follow-up (AI should remember context)
curl -X POST http://localhost:8000/api/v0/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Has it changed recently?",
    "patient_id": "123",
    "session_id": "test-session-uuid"
  }'

# 4. Clear conversation
curl -X DELETE http://localhost:8000/api/v0/chat/history/test-session-uuid
```

### Frontend Testing

**Browser Console Tests:**
```javascript
// Check session persistence
localStorage.getItem('chat_session_123')

// Verify API calls
// Open DevTools > Network tab
// Filter by "dashboard" or "chat"
// Check request/response payloads
```

**UI Testing Checklist:**
- [ ] Patient list loads quickly (1-2 seconds)
- [ ] Pagination controls visible when > 20 patients
- [ ] Page navigation buttons work correctly
- [ ] Page size selector changes results
- [ ] "Showing X to Y of Z" displays correctly
- [ ] Search functionality works
- [ ] Click patient opens dashboard
- [ ] Chat interface loads
- [ ] AI responds to questions
- [ ] Refresh page preserves conversation
- [ ] Follow-up questions show context understanding
- [ ] Clear conversation button works
- [ ] Confirmation dialog appears before clearing

### Automated Testing

**Backend Tests:**
```bash
cd backend/engine
poetry run pytest

cd backend/patient_data
poetry run pytest
```

**Frontend Tests:**
```bash
cd frontend
npm run test
```

## 🐛 Troubleshooting

### Common Issues

**1. Services won't start**
```bash
# Check if ports are already in use
lsof -i :3000  # Frontend
lsof -i :8000  # Engine
lsof -i :8001  # Patient Data
lsof -i :8003  # Biomedical LLM

# Kill processes if needed
kill -9 <PID>

# Or use different ports in docker-compose.yml
```

**2. Docker build fails**
```bash
# Clean Docker cache and rebuild
docker system prune -a
make clean
make build
```

**3. Frontend can't connect to backend**
```bash
# Check CORS settings in backend
# Verify API_BASE_URL in frontend/.env
# Check Docker network: docker network inspect mendai_default
```

**4. OpenAI API errors**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check backend logs
make logs-engine

# Common errors:
# - "Invalid API key" → Check .env file
# - "Rate limit exceeded" → Reduce request frequency
# - "Model not found" → Verify model name (gpt-4o-mini)
```

**5. Conversation not persisting**
```bash
# Check localStorage in browser
# DevTools > Application > Local Storage
# Look for keys like: chat_session_${patientId}

# Check session exists in backend
curl http://localhost:8000/api/v0/chat/stats

# Clear browser cache and test again
```

**6. Pagination not working**
```bash
# Verify backend returns pagination metadata
curl "http://localhost:8000/api/v0/dashboard?page=1&page_size=20" | jq

# Expected response should include:
# - total
# - page
# - page_size
# - total_pages
```

**7. Performance issues**
```bash
# Check Docker resource limits
docker stats

# Increase Docker memory/CPU in Docker Desktop settings
# Recommended: 4GB RAM, 2 CPUs minimum

# Check logs for errors
make logs
```

### Debug Mode

**Enable verbose logging:**
```bash
# Edit backend/engine/.env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart services
make restart

# View detailed logs
make logs-engine
```

**Frontend debug:**
```javascript
// Add to browser console
localStorage.setItem('debug', '*')
// Reload page to see debug logs
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

1. **Fork and Clone**
```bash
git clone https://github.com/YOUR_USERNAME/MendAI.git
cd MendAI
git remote add upstream https://github.com/ricktruong/MendAI.git
```

2. **Create Feature Branch**
```bash
git checkout -b feature/your-amazing-feature
```

3. **Make Changes**
- Follow existing code style
- Add tests for new features
- Update documentation
- Test thoroughly (frontend + backend)

4. **Commit Changes**
```bash
git add .
git commit -m "Add amazing feature: brief description"
```

5. **Push and Create PR**
```bash
git push origin feature/your-amazing-feature
# Open Pull Request on GitHub
```

### Code Style Guidelines

**Python (Backend):**
- Use Black for formatting: `black .`
- Follow PEP 8 conventions
- Add type hints to functions
- Write docstrings for classes/functions
- Use async/await for I/O operations

**TypeScript (Frontend):**
- Use ESLint and Prettier
- Follow functional component patterns
- Use TypeScript types (avoid `any`)
- Add JSDoc comments for complex functions

### Testing Requirements

- Add unit tests for new backend endpoints
- Test frontend components
- Verify Docker builds
- Check all health endpoints
- Test pagination with edge cases
- Test conversation memory persistence

## 📚 Additional Documentation

### Feature Documentation
- [Conversation Memory Feature](CONVERSATION_MEMORY_FEATURE.md) - Architecture and API reference
- [Conversation Memory Testing](CONVERSATION_MEMORY_TEST_GUIDE.md) - Step-by-step testing guide

### Service Documentation
- [Frontend README](frontend/README.md) - Frontend development guide
- [Engine Service](backend/engine/README.md) - Main API gateway documentation
- [Patient Data Service](backend/patient_data/README.md) - FHIR integration guide
- [Biomedical LLM Service](backend/biomedical_llm/README.md) - LLM service documentation

### Quick Reference
- **Make Commands**: Run `make help` to see all available commands
- **API Documentation**: Visit `http://localhost:8000/docs` when services are running
- **Docker Logs**: Use `make logs` or `docker-compose logs -f [service-name]`

## 🎓 Learning Resources

### For Healthcare Professionals
- **FHIR Standard**: https://www.hl7.org/fhir/
- **DICOM Format**: https://www.dicomstandard.org/
- **Medical AI**: https://monai.io/

### For Developers
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Docker**: https://docs.docker.com/
- **OpenAI API**: https://platform.openai.com/docs/

## 📊 Project Status

### Completed Features ✅
- ✅ Patient data management with FHIR integration
- ✅ Medical imaging analysis with DICOM support
- ✅ AI-powered chat with GPT-4o-mini
- ✅ Conversation memory system (24hr TTL, session-based)
- ✅ High-performance pagination (80% faster load times)
- ✅ Real-time chat interface
- ✅ Age calculation fix for FHIR dates
- ✅ Docker containerization
- ✅ Auto-reload in development
- ✅ Comprehensive documentation

### In Progress 🚧
- 🚧 Persistent conversation storage (Redis/PostgreSQL)
- 🚧 User authentication and authorization
- 🚧 Advanced medical image analysis
- 🚧 Multi-model LLM support
- 🚧 Export/import patient data

### Planned Features 📋
- 📋 Role-based access control (RBAC)
- 📋 Audit logging for compliance
- 📋 Real-time notifications
- 📋 Mobile application
- 📋 Advanced analytics dashboard
- 📋 Integration with more EHR systems
- 📋 Multi-language support

## 📄 License

This project is for educational and research purposes.

**Important Notes:**
- Medical AI models are for research only
- Not FDA approved for clinical use
- Requires proper credentials for production FHIR access
- OpenAI API usage subject to OpenAI terms of service

## 🆘 Support & Contact

### Getting Help

1. **Check Documentation**: Start with this README and feature-specific docs
2. **Review Issues**: Check [GitHub Issues](https://github.com/ricktruong/MendAI/issues) for similar problems
3. **Service Logs**: Use `make logs` to check for errors
4. **Health Checks**: Run `make health` to verify all services
5. **Community**: Open a new issue with detailed information

### Reporting Issues

When reporting bugs, please include:
- Operating system and version
- Docker version (`docker --version`)
- Steps to reproduce
- Error messages and logs
- Expected vs actual behavior

### Feature Requests

We welcome feature suggestions! Please:
- Check existing issues first
- Describe the use case
- Explain expected behavior
- Consider implementation complexity

## 🙏 Acknowledgments

- **MONAI Framework** - Medical imaging AI
- **OpenAI** - GPT-4o-mini language model
- **FastAPI Team** - High-performance web framework
- **React Team** - Frontend framework
- **Google Healthcare** - FHIR API integration
- **Healthcare Community** - Domain expertise and feedback

## 📞 Contact

- **Project Repository**: https://github.com/ricktruong/MendAI
- **Issues**: https://github.com/ricktruong/MendAI/issues
- **Email**: [Contact project maintainers]

---

**Built with ❤️ for better healthcare outcomes**

*Last Updated: November 16, 2025*
