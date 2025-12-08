# MendAI: AI-Powered Clinical Decision Support System

MendAI is an intelligent healthcare assistant that integrates seamlessly with hospital EHR systems, patient data, medical imaging, laboratory results, and clinical documentation. It provides healthcare professionals with AI-assisted diagnostic insights within a unified workflow.

## Overview

MendAI leverages advanced AI technologies to enhance clinical decision-making through real-time patient data analysis, medical imaging interpretation, and natural language interaction. The system combines FHIR-compliant data management with state-of-the-art language models to deliver contextual, patient-specific insights.

## Key Features

### Intelligent Conversation System
- **Persistent Context**: Maintains conversation history throughout patient sessions
- **Session Management**: Automatic 24-hour session lifecycle with cleanup
- **Smart Memory**: Token-optimized context window (2000 tokens max)
- **Patient Isolation**: Separate conversation threads for each patient
- **User Control**: Manual conversation clearing with confirmation

### High-Performance Patient Management
- **Optimized Loading**: Default 20-patient pagination (80% faster than bulk loading)
- **Flexible Views**: Configurable page sizes (10/20/50/100 patients)
- **Intuitive Navigation**: Full pagination controls with smart page ranges
- **Fast Search**: Real-time patient search across all fields
- **CRUD Operations**: Complete patient record management

### Medical Imaging Analysis
- **NIfTI Support**: CT scan processing and analysis (NIfTI format)
- **Batch Processing**: Multi-image analysis capabilities
- **Slice Analysis**: Detailed examination of individual scan slices
- **AI Integration**: MONAI-powered medical image interpretation
- **Visual Display**: Base64-encoded image rendering in browser

### Clinical AI Assistant
- **GPT-4o Integration**: Advanced language model for medical queries
- **Contextual Responses**: Full access to patient FHIR data
- **Real-Time Chat**: Instant responses to clinical questions
- **Specialized Prompts**: Clinical knowledge-optimized prompting

## Architecture

MendAI follows a microservices architecture with dedicated services for different functionalities:

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
│FHIR API │ │NIfTI/MONAI   │ │GPT-4o-mini   │ │24hr TTL      │
└─────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Components

- **Frontend**: React 18 + TypeScript + Vite
- **API Gateway**: FastAPI engine with service orchestration
- **Patient Data Service**: FHIR-compliant patient information management
- **Medical Imaging Service**: MONAI-powered medical image analysis (NIfTI)
- **Biomedical LLM Service**: GPT-4o-mini with clinical prompting
- **Conversation Manager**: Session-based context retention

## Project Structure

```
MendAI/
├── frontend/                # React application
│   ├── src/                 # Source code
│   ├── Dockerfile           # Frontend container
│   └── nginx.conf           # Web server configuration
├── backend/
│   ├── engine/              # API gateway and routing
│   ├── patient_data/        # FHIR data service
│   ├── medical_imaging/     # Medical image processing service (NIfTI)
│   ├── biomedical_llm/      # Language model service
│   └── common/              # Shared utilities
├── docker-compose.yml       # Container orchestration
├── Makefile                 # Build and management commands
└── README.md               # This file
```

## Quick Start

### Prerequisites

**Required:**
- Docker Desktop (v20.10+) - [Download](https://www.docker.com/products/docker-desktop)
- Docker Compose (v2.0+) - Included with Docker Desktop
- Git - For repository cloning

**Optional (for local development):**
- Python 3.9+ - Backend development
- Node.js 18+ - Frontend development
- Poetry - Python dependency management

**Configuration Requirements:**
- OpenAI API Key - Required for LLM functionality
- Google Cloud Credentials - Required for FHIR data access

### Installation

#### Docker Deployment (Recommended)

1. **Clone Repository**
```bash
git clone https://github.com/ricktruong/MendAI.git
cd MendAI
```

2. **Run Setup Script**
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Verify prerequisites (Docker, Node.js, Python, Poetry)
- Clean Docker cache and resolve common issues
- Generate environment configuration files
- Install backend dependencies via Poetry
- Install frontend dependencies via npm
- Validate project structure
- Optionally test Docker builds

3. **Configure Environment**

Edit environment files with your credentials:

```bash
# Backend Engine - OpenAI API Key
nano backend/engine/.env
# Add: OPENAI_API_KEY=sk-your-api-key-here

# Patient Data Service - Google Cloud
nano backend/patient_data/.env
# Add: GOOGLE_CLOUD_PROJECT=your-project-id
#      GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

4. **Start Services**
```bash
make build
make up

# View logs
make logs
```

5. **Access Application**
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Patient Data API: http://localhost:8001/docs
- Biomedical LLM API: http://localhost:8003/docs

6. **Verify Health**
```bash
make health

# Or manually:
curl http://localhost:8000/health  # Engine
curl http://localhost:8001/health  # Patient Data
curl http://localhost:8003/health  # Biomedical LLM
```

#### Local Development

For active development with hot-reload:

1. **Clone and Setup**
```bash
git clone https://github.com/ricktruong/MendAI.git
cd MendAI
./setup.sh
```

2. **Start Backend Services** (4 separate terminals)

Terminal 1 - Patient Data Service:
```bash
cd backend/patient_data
poetry install
poetry run uvicorn patient_data.main:app --port 8001 --reload
```

Terminal 2 - Biomedical LLM Service:
```bash
cd backend/biomedical_llm
poetry install
export PATIENT_DATA_URL=http://localhost:8001
poetry run uvicorn biomedical_llm.main:app --port 8003 --reload
```

Terminal 3 - Engine Service:
```bash
cd backend/engine
poetry install
export PATIENT_DATA_SERVICE_URL=http://localhost:8001
export BIOMEDICAL_LLM_URL=http://localhost:8003
poetry run uvicorn engine.main:app --port 8000 --reload
```

Terminal 4 - Frontend:
```bash
cd frontend
npm install
npm run dev
```

3. **Access Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

### Management Commands

```bash
make help          # Display all available commands
make build         # Build Docker images
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make logs          # View all service logs
make logs-engine   # View engine logs
make logs-frontend # View frontend logs
make status        # Check service status
make health        # Verify service health
make clean         # Remove containers and volumes
```

### GPU Support (Optional)

For AI/ML acceleration with NVIDIA GPU:

```bash
# Install NVIDIA Docker Runtime:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

make gpu-build
make gpu-up
```

## Services & Ports

### Frontend (Port 3000)
**Technology**: React 18 + TypeScript + Vite

**Features**:
- Paginated patient list with configurable page sizes
- Real-time patient dashboard with integrated chat
- Persistent conversation memory via localStorage
- Responsive healthcare workflow design
- Hot module replacement in development

### Backend Engine (Port 8000)
**Technology**: FastAPI + Python 3.9+

**Features**:
- API gateway and request routing
- Session-based conversation management
- Pagination logic for patient data
- Service orchestration and health monitoring

**Key Endpoints**:
- `GET /api/v0/dashboard?page=1&page_size=20` - Paginated patient list
- `POST /api/v0/chat` - Chat with conversation memory
- `GET /api/v0/chat/history/{session_id}` - Retrieve conversation
- `DELETE /api/v0/chat/history/{session_id}` - Clear conversation
- `GET /api/v0/chat/stats` - Conversation statistics
- `GET /health` - Service health check

### Patient Data Service (Port 8001)
**Technology**: FastAPI + Google Healthcare FHIR API

**Features**:
- FHIR-compliant patient data access
- Patient record CRUD operations
- Biometric and medical history management
- Corrected FHIR date handling for accurate age calculation

**Key Endpoints**:
- `GET /api/v0/patients` - List all patients
- `GET /api/v0/patients/{id}` - Get patient details
- `POST /api/v0/patients` - Create patient
- `PUT /api/v0/patients/{id}` - Update patient
- `DELETE /api/v0/patients/{id}` - Delete patient
- `GET /health` - Service health check

### Medical Imaging Service (Port 8002)
**Technology**: FastAPI + MONAI + PyTorch

**Features**:
- NIfTI file processing and conversion
- CT scan segmentation and analysis
- Batch and slice-based image processing
- Base64 image encoding for frontend display
- AI-powered disease detection

**Key Endpoints**:
- `POST /api/v0/imaging/analyze` - Analyze medical images
- `POST /api/v0/imaging/batch` - Batch processing
- `POST /api/v0/imaging/convert` - Medical image conversion
- `GET /health` - Service health check

### Biomedical LLM Service (Port 8003)
**Technology**: FastAPI + OpenAI GPT-4o-mini

**Features**:
- Medical question answering with clinical prompts
- Patient context integration (FHIR data)
- Real-time chat responses
- Token-optimized context management

**Key Endpoints**:
- `POST /api/v0/chat` - Chat with biomedical LLM
- `POST /api/v0/analyze` - Analyze patient case
- `GET /health` - Service health check

**Configuration**:
- Requires `OPENAI_API_KEY` environment variable
- Uses GPT-4o-mini for cost-effective responses
- Specialized clinical prompting for accuracy

## Technology Stack

### Frontend
- React 18 - UI framework
- TypeScript - Type-safe development
- Vite - Fast build tool
- Axios - HTTP client
- CSS Modules - Component styling
- localStorage - Client-side persistence

### Backend
- FastAPI - Async web framework
- Python 3.9+ - Core language
- Poetry - Dependency management
- Uvicorn - ASGI server
- Pydantic - Data validation
- httpx - Async HTTP client

### AI & ML
- OpenAI GPT-4o-mini - Language model
- MONAI - Medical imaging AI
- PyTorch - Deep learning framework
- Transformers - Model library
- NumPy/SciPy - Scientific computing

### Data & Integration
- Google Healthcare FHIR API - Patient data
- DICOM - Medical imaging standard
- REST APIs - Service communication
- JSON - Data interchange

### Infrastructure
- Docker - Containerization
- Docker Compose - Orchestration
- Nginx - Web server
- Make - Build automation
- Git - Version control

## System Features

### Conversation Memory

The conversation system maintains context throughout patient sessions:

**Architecture**:
- In-memory session storage with UUID-based session IDs
- 24-hour automatic session expiration
- Maximum 2000 tokens per context window
- Up to 50 messages per session
- localStorage persistence on client side

**Workflow**:
1. Patient dashboard opens → Session ID generated or restored
2. User asks question → Message stored before LLM call
3. AI responds → Response stored in conversation history
4. Page refresh → Session restored from localStorage
5. Context maintained → AI remembers previous exchanges

**API Endpoints**:
```bash
GET /api/v0/chat/history/{session_id}      # Retrieve history
DELETE /api/v0/chat/history/{session_id}   # Clear conversation
GET /api/v0/chat/stats                     # System statistics
```

**Frontend Integration**:
- Session management in `PatientDashboardPage.tsx`
- localStorage key: `chat_session_${patientId}`
- Confirmation dialog for conversation clearing
- Auto-restoration on component mount

**Configuration**:
```python
# backend/engine/services/conversation_manager.py
MAX_MESSAGES_PER_SESSION = 50
SESSION_TTL_HOURS = 24
MAX_CONTEXT_TOKENS = 2000
```

### Pagination System

High-performance pagination improves initial load time by 80%:

**Backend Implementation**:
```python
@router.get("/dashboard")
async def get_patient_list_data(
    page: int = 1,
    page_size: int = 20
):
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)

    return {
        "patients": patients[start_idx:end_idx],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size)
    }
```

**Frontend Implementation**:
- State management for current page and page size
- Dynamic data loading on page change
- UI controls: First/Previous/Next/Last navigation
- Page size selector (10/20/50/100)
- Smart page range display (5 pages at a time)
- Loading state management

**Performance**:
- Before: 5-10 seconds for 100 patients
- After: 1-2 seconds for 20 patients
- Improvement: 80% faster initial load

## Monitoring & Health Checks

All services expose health check endpoints:

```bash
# Check all services
make health

# Individual checks
curl http://localhost:8000/health    # Engine
curl http://localhost:8001/health    # Patient Data
curl http://localhost:8002/health    # Medical Imaging
curl http://localhost:8003/health    # Biomedical LLM
```

**Health Response**:
```json
{
  "status": "healthy",
  "service": "engine",
  "version": "1.0.0",
  "timestamp": "2025-11-16T12:00:00Z"
}
```

**Service Logs**:
```bash
make logs                # All services
make logs-engine         # Engine only
make logs-frontend       # Frontend only
docker-compose logs -f   # Real-time
```

**Conversation Statistics**:
```bash
curl http://localhost:8000/api/v0/chat/stats

# Response:
{
  "total_sessions": 15,
  "active_sessions": 8,
  "total_messages": 234,
  "avg_messages_per_session": 15.6
}
```

## Security & Best Practices

### Environment Configuration

All sensitive data stored in environment files (gitignored):

**Backend Engine** (`backend/engine/.env`):
```bash
OPENAI_API_KEY=sk-your-openai-api-key
PATIENT_DATA_SERVICE_URL=http://localhost:8001
BIOMEDICAL_LLM_URL=http://localhost:8003
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

**Patient Data Service** (`backend/patient_data/.env`):
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
SERVICE_PORT=8001
```

**Biomedical LLM Service** (`backend/biomedical_llm/.env`):
```bash
OPENAI_API_KEY=sk-your-openai-api-key
PATIENT_DATA_URL=http://localhost:8001
SERVICE_PORT=8003
```

### Container Security
- Non-root users in all containers
- Network isolation between services
- Read-only file systems where applicable
- Minimal base images (Alpine Linux)
- No hardcoded secrets

### API Security
- CORS configuration for frontend
- Pydantic request validation
- Environment-based configuration
- Health endpoints (no authentication required)
- **Production TODO**: Implement JWT authentication

## Production Deployment

### Pre-Production Checklist

- [ ] Set `ENVIRONMENT=production` in all `.env` files
- [ ] Set `DEBUG=false` in all `.env` files
- [ ] Generate strong production secrets
- [ ] Configure `LOG_LEVEL=WARNING`
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Implement monitoring and alerting
- [ ] Configure backup strategy
- [ ] Review and restrict CORS settings
- [ ] Set up CI/CD pipeline

### Docker Production

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Start services
docker-compose up -d

# Scale services
docker-compose up -d --scale engine=2 --scale llm=2
```

### Production Environment

```bash
# backend/engine/.env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
OPENAI_API_KEY=sk-prod-key
SECRET_KEY=strong-secret-key
JWT_SECRET=jwt-secret
ALLOWED_ORIGINS=https://yourdomain.com
```

### Scaling

**Horizontal Scaling**:
```bash
docker-compose up -d --scale engine=3
docker-compose up -d --scale llm=2
```

**Load Balancing**:
- Use Nginx or Traefik
- Configure health checks for failover
- Implement sticky sessions for conversation memory

**Database Migration**:
- Current: In-memory conversation storage
- **Production TODO**: Migrate to Redis or PostgreSQL
- Implement session replication

## Testing

### Quick Validation

```bash
# Test pagination
curl "http://localhost:8000/api/v0/dashboard?page=1&page_size=20"

# Test conversation memory
curl -X POST http://localhost:8000/api/v0/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the patient'\''s blood pressure?",
    "patient_id": "123",
    "session_id": "test-session-uuid"
  }'

# Retrieve conversation
curl http://localhost:8000/api/v0/chat/history/test-session-uuid

# Clear conversation
curl -X DELETE http://localhost:8000/api/v0/chat/history/test-session-uuid
```

### Frontend Testing

**Browser Console**:
```javascript
// Check session persistence
localStorage.getItem('chat_session_123')
```

**UI Checklist**:
- [ ] Patient list loads within 2 seconds
- [ ] Pagination controls display correctly
- [ ] Page navigation functions properly
- [ ] Page size selector works
- [ ] Search operates correctly
- [ ] Patient dashboard opens successfully
- [ ] Chat interface loads
- [ ] AI responds to queries
- [ ] Page refresh maintains conversation
- [ ] Follow-up questions show context retention
- [ ] Clear conversation works with confirmation

### Automated Testing

```bash
# Backend tests
cd backend/engine
poetry run pytest

cd backend/patient_data
poetry run pytest

# Frontend tests
cd frontend
npm run test
```

### E2E Testing Framework

MendAI includes a comprehensive end-to-end testing framework using Playwright.

**Test Coverage**:
- 19 comprehensive tests across 2 test suites
- 100% pass rate
- Full system validation (all 5 services)
- API integration tests (Slice & Batch Analysis)
- Performance benchmarking
- AI model validation

**Quick Start**:
```bash
cd frontend

# Validate medical imaging test data
npm run validate-images

# Run all E2E tests
npm run test:e2e

# Run specific test suite
npm run test:e2e -- basic-flow.spec.ts          # 9 tests, ~45s
npm run test:e2e -- complete-success.spec.ts    # 10 tests, ~1m

# Interactive mode
npm run test:e2e:ui

# View test report
npm run test:e2e:report
```

**Test Suites**:
1. **Basic Flow Tests** (`basic-flow.spec.ts`)
   - Service health checks (all 5 services)
   - API endpoint validation
   - Service integration tests
   - Duration: ~45 seconds

2. **Complete Success Suite** (`complete-success.spec.ts`)
   - Full system validation
   - Medical imaging data validation
   - Slice and batch analysis APIs
   - AI model validation
   - Performance metrics
   - Duration: ~1 minute

**Performance Results**:
- Slice Analysis: 3.5s (target: <10s)
- Batch Analysis: 35s (target: <60s)
- Health Checks: <1s (target: <2s)
- Frontend Load: 1.5s (target: <5s)

**Documentation**:
- [Testing Quick Start](e2e-docs/TESTING_QUICKSTART.md) - 5-minute guide
- [Testing Certification](e2e-docs/TESTING_CERTIFICATION.md) - Full certification report
- [E2E Testing Guide](e2e-docs/E2E_TESTING_GUIDE.md) - Complete testing guide
- [Test Results Summary](e2e-docs/TEST_RESULTS_SUMMARY.md) - Detailed results

**Prerequisites**:
```bash
# Install Playwright browsers (first time only)
npx playwright install chromium
```

**Test Data Setup**:
Place your NIfTI medical imaging test files in:
```
frontend/tests/e2e/fixtures/medical-data/
├── case-001/  # Your .nii files here
└── case-002/  # Your .nii files here
```

**Verify Backend Services**:
```bash
# Windows
scripts\verify-backend.bat

# Linux/Mac
scripts/verify-backend.sh
```

## Troubleshooting

### Port Conflicts

```bash
# Check port usage
lsof -i :3000  # Frontend
lsof -i :8000  # Engine
lsof -i :8001  # Patient Data
lsof -i :8003  # Biomedical LLM

# Terminate process
kill -9 <PID>
```

### Docker Build Issues

```bash
# Clean cache and rebuild
docker system prune -a
make clean
make build
```

### Frontend Connection Issues

- Verify CORS settings in backend
- Check `API_BASE_URL` in frontend/.env
- Inspect Docker network: `docker network inspect mendai_default`

### OpenAI API Errors

```bash
# Verify API key
echo $OPENAI_API_KEY

# Check logs
make logs-engine

# Common issues:
# - Invalid API key → Check .env file
# - Rate limit → Reduce request frequency
# - Model not found → Verify model name (gpt-4o-mini)
```

### Conversation Persistence Issues

- Check localStorage in browser DevTools (Application > Local Storage)
- Verify backend session: `curl http://localhost:8000/api/v0/chat/stats`
- Clear browser cache and retry

### Performance Issues

```bash
# Monitor Docker resources
docker stats

# Increase resources in Docker Desktop
# Recommended: 4GB RAM, 2 CPUs minimum

# Check logs for errors
make logs
```

### Debug Mode

**Enable verbose logging**:
```bash
# Edit backend/engine/.env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart and view logs
make restart
make logs-engine
```

**Frontend debug**:
```javascript
// Browser console
localStorage.setItem('debug', '*')
// Reload page
```

## Contributing

### Development Workflow

1. **Fork and Clone**
```bash
git clone https://github.com/YOUR_USERNAME/MendAI.git
cd MendAI
git remote add upstream https://github.com/ricktruong/MendAI.git
```

2. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

3. **Develop**
- Follow existing code style
- Add tests for new features
- Update documentation
- Test thoroughly

4. **Commit and Push**
```bash
git add .
git commit -m "Add feature: description"
git push origin feature/your-feature-name
```

5. **Create Pull Request**
Open PR on GitHub with detailed description

### Code Style

**Python (Backend)**:
- Use Black for formatting: `black .`
- Follow PEP 8 conventions
- Add type hints
- Write docstrings
- Use async/await for I/O

**TypeScript (Frontend)**:
- Use ESLint and Prettier
- Follow functional component patterns
- Use TypeScript types (avoid `any`)
- Add JSDoc for complex functions

### Testing Requirements

- Add unit tests for backend endpoints
- Test frontend components
- Verify Docker builds
- Check health endpoints
- Test edge cases

## Documentation

### Feature Documentation
- [Conversation Memory Feature](CONVERSATION_MEMORY_FEATURE.md) - Architecture and API
- [Conversation Memory Testing](CONVERSATION_MEMORY_TEST_GUIDE.md) - Testing guide

### Service Documentation
- [Frontend README](frontend/README.md) - Frontend development
- [Engine Service](backend/engine/README.md) - API gateway
- [Patient Data Service](backend/patient_data/README.md) - FHIR integration
- [Biomedical LLM Service](backend/biomedical_llm/README.md) - LLM service

### Quick Reference
- **Make Commands**: `make help`
- **API Documentation**: http://localhost:8000/docs (when running)
- **Docker Logs**: `make logs` or `docker-compose logs -f [service]`

## Resources

### Healthcare Standards
- FHIR Standard: https://www.hl7.org/fhir/
- DICOM Format: https://www.dicomstandard.org/
- Medical AI: https://monai.io/

### Development
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Docker: https://docs.docker.com/
- OpenAI API: https://platform.openai.com/docs/

## Project Status

### Completed
- Patient data management with FHIR integration
- Medical imaging analysis with NIfTI support
- AI-powered chat with GPT-4o-mini
- Conversation memory system (24hr TTL, session-based)
- High-performance pagination (80% faster)
- Real-time chat interface
- FHIR date handling fixes
- Docker containerization
- Auto-reload in development
- Comprehensive documentation


### Planned
- Role-based access control (RBAC)
- Audit logging for compliance
- Real-time notifications
- Mobile application
- Advanced analytics dashboard
- Additional EHR system integrations
- Multi-language support

## License

This project is for educational and research purposes.

**Important Notes**:
- Medical AI models are research-grade only
- Not FDA approved for clinical use
- Requires proper credentials for production FHIR access
- OpenAI API usage subject to OpenAI terms of service

## Support

### Getting Help

1. Check this README and feature-specific documentation
2. Review [GitHub Issues](https://github.com/ricktruong/MendAI/issues)
3. Check service logs: `make logs`
4. Verify service health: `make health`
5. Open new issue with detailed information

### Reporting Issues

Include:
- Operating system and version
- Docker version (`docker --version`)
- Steps to reproduce
- Error messages and logs
- Expected vs actual behavior

### Feature Requests

- Check existing issues first
- Describe the use case
- Explain expected behavior
- Consider implementation complexity

## Acknowledgments

- MONAI Framework - [Medical Imaging AI](https://huggingface.co/datasets/ibrahimhamamci/CT-RATE)
- OpenAI - GPT-4o-mini language model
- FastAPI Team - Web framework
- React Team - Frontend framework
- Google Healthcare - FHIR API integration
- Healthcare Community - Domain expertise

## Contact

- Repository: https://github.com/ricktruong/MendAI
- Issues: https://github.com/ricktruong/MendAI/issues

---

**Built with care for better healthcare outcomes**

*Last Updated: November 27, 2025*
