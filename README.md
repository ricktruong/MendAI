# MendAI: Your Agentic AI Healthcare Assistant

A comprehensive healthcare application that enables healthcare professionals to access patient data, process medical scans, analyze laboratory results, and receive AI-assisted patient prognosis through a seamless, integrated medical workflow platform.

## 🏗️ Architecture

```
[ React Frontend (Vite, TSX) ]
            |
            v
[ Backend Engine (FastAPI) ]
            |
    -------------------------------
    |             |               |
    v             v               v
[Patient   [Medical Imaging] [Biomedical LLM]
 Data]         Service         Service
 Service
```

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
│   ├── imaging/             # Medical imaging service (MONAI)
│   ├── biomedical_llm/      # LLM service (MONAI + Transformers)
│   ├── common/              # Shared code and utilities
│   └── docker-compose.yml   # Backend services orchestration
├── docker-compose.yml       # Complete application orchestration
├── Makefile                 # Management commands
└── README.md               # This file
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

#### Prerequisites
- Docker
- Docker Compose
- NVIDIA Docker Runtime (for GPU support - optional)

#### Setup

**Development (CPU-only):**
```bash
# Clone the repository
git clone <repository-url>
cd MendAI

# Start all services with CPU-only containers
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

**Production with GPU Support:**
```bash
# Start all services with GPU-enabled containers for medical_imaging and biomedical_llm
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

**Production (CPU-only):**
```bash
# Start all services with production CPU containers
docker-compose up --build
```

#### Management Commands
```bash
make help          # Show all available commands
make build         # Build all Docker images
make up            # Start all services
make down          # Stop all services
make logs          # View logs
make status        # Check service status
make health        # Check service health
```

#### Docker Configuration
- `docker-compose.yml` - Main configuration with all services (CPU-only)
- `docker-compose.gpu.yml` - GPU-enabled overrides for medical_imaging and biomedical_llm

For detailed Docker setup instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

### Option 2: Local Development

#### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.9+ (for backend services)
- Poetry (for Python dependency management)

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Backend Services Setup

Each service can be run independently:

```bash
# Backend Engine
cd backend/engine
poetry install
poetry run uvicorn engine.main:app --host 0.0.0.0 --port 8000

# Patient Data Service
cd backend/patient_data
poetry install
poetry run uvicorn patient_data.main:app --host 0.0.0.0 --port 8001

# Imaging Service
cd backend/imaging
poetry install
poetry run uvicorn imaging.main:app --host 0.0.0.0 --port 8002

# Biomedical LLM Service
cd backend/biomedical_llm
poetry install
poetry run uvicorn biomedical_llm.main:app --host 0.0.0.0 --port 8003
```

## 🔧 Services

### Frontend (Port 3000)
- React-based user interface
- TypeScript for type safety
- Vite for fast development
- Responsive design for healthcare workflows

### Backend Engine (Port 8000)
- API gateway and routing
- Authentication and authorization
- Request aggregation
- Service orchestration
- Health monitoring

### Patient Data Service (Port 8001)
- Epic FHIR API integration
- Patient data storage and retrieval
- Biometric data management
- Medical history tracking
- Secure data handling

### Medical Imaging Service (Port 8002)
- DICOM file processing
- Medical image segmentation
- Disease detection and classification
- MONAI model integration
- Image preprocessing and analysis

### Biomedical LLM Service (Port 8003)
- Multimodal image-text processing
- Biomedical chatbot functionality
- AI-assisted patient prognosis
- Clinical text analysis
- Medical knowledge integration

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **CSS Modules** - Component styling

### Backend
- **FastAPI** - Web framework for all services
- **Poetry** - Dependency management
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Medical Imaging
- **MONAI** - Medical AI framework
- **PyTorch** - Deep learning framework
- **DICOM** - Medical image formats

### AI/ML
- **Transformers** - HuggingFace transformers library
- **MONAI** - Multimodal medical AI
- **NumPy/SciPy** - Scientific computing

### Data Integration
- **Epic FHIR API** - Patient data integration
- **REST APIs** - Service communication

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Service orchestration
- **Nginx** - Frontend web server

## 🔍 Monitoring & Health Checks

All services include health check endpoints:
- Frontend: `http://localhost:3000/health`
- Backend Engine: `http://localhost:8000/health`
- Patient Data: `http://localhost:8001/health`
- Imaging: `http://localhost:8002/health`
- Biomedical LLM: `http://localhost:8003/health`

## 🔒 Security Features

- Non-root container users
- Network isolation between services
- Health monitoring
- Secure API endpoints
- Environment variable configuration

## 🚀 Production Deployment

### Environment Variables
Create `.env` files for each service:
```bash
# Example: backend/engine/.env
LOG_LEVEL=WARNING
DATABASE_URL=your_database_url
API_KEY=your_api_key
```

### Scaling
```bash
# Scale specific services
docker-compose up -d --scale imaging=2
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Submit a pull request

## 📚 Documentation

- [Docker Setup Guide](DOCKER_README.md) - Detailed Docker deployment instructions
- [Frontend README](frontend/README.md) - Frontend development guide
- [Backend Service READMEs](backend/) - Individual service documentation

## 📄 License

This project is for educational and research purposes.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section in the Docker README
2. Review service-specific documentation
3. Check service logs: `make logs`
4. Verify service health: `make health`
