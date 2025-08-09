# MendAI: A Multimodal AI Assistant for Smarter Clinical Decision-Making

MendAI, your agentic AI healthcare assistant, seamlessly integrates with your hospital’s EHR system, patients’ data, medical scans, laboratory results, and clinical text, to give to healthcare professionals like you AI-assisted patient prognosis all within one seamless, integrated medical workflow solution.
- Customer: Hospital/healthcare professionals
- Project Direction: Application which speeds up doctors diagnoses and work (medical scan processing, biometric data analysis, medical notes analysis) + scientists can manage the models our application provides, finetune, enhance to match hospitals' and patients' needs

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
│   ├── medical_imaging/     # Medical imaging service (MONAI)
│   ├── biomedical_llm/      # LLM service (MONAI + Transformers)
│   └── common/              # Shared code and utilities
├── docker-compose.yml       # Complete application orchestration
├── Makefile                 # Management commands
└── README.md               # This file
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

#### Prerequisites

**Required:**
- **Docker Desktop** - Download from [docker.com](https://www.docker.com/products/docker-desktop)
- **Docker Compose** - Included with Docker Desktop

**Optional (for local development):**
- **Python 3.9+** - Required for backend local development
- **Node.js 18+** - Required for frontend local development  
- **Poetry** - Python dependency management (`curl -sSL https://install.python-poetry.org | python3 -`)

#### Setup

**Automated Setup (Recommended):**
```bash
# Clone the repository
git clone <repository-url>
cd MendAI

# Run the automated setup script
./setup.sh

# Start all services
make up

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

The setup script will:
- Check all prerequisites
- Create environment files for each service
- Set up backend and frontend dependencies
- Validate the project structure
- Optionally test Docker builds

**Manual Setup:**
```bash
# If you prefer manual setup or the script fails
make build    # Build all images
make up       # Start all services
```

**GPU Support (for AI/ML acceleration):**
```bash
# Requires NVIDIA Docker Runtime
# Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
make gpu-build
make gpu-up
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

**Troubleshooting:**
- If Docker build fails, run `./setup.sh` to check prerequisites and fix common issues
- Use `make logs` to view service logs
- Use `make health` to check service status
- Environment files are automatically created in each service directory

### Option 2: Local Development

#### Prerequisites
- **Node.js 18+** - For frontend development
- **Python 3.9+** - For backend services
- **Poetry** - Python dependency management

**Install Poetry:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Backend Services Setup

Each service can be run independently:

```bash
# Backend Engine (Main API Gateway)
cd backend/engine
poetry install
poetry run uvicorn engine.main:app --host 0.0.0.0 --port 8000

# Patient Data Service
cd backend/patient_data
poetry install
poetry run uvicorn patient_data.main:app --host 0.0.0.0 --port 8001

# Medical Imaging Service
cd backend/medical_imaging
poetry install
poetry run uvicorn medical_imaging.main:app --host 0.0.0.0 --port 8002

# Biomedical LLM Service
cd backend/biomedical_llm
poetry install
poetry run uvicorn biomedical_llm.main:app --host 0.0.0.0 --port 8003
```

**Note:** The setup script (`./setup.sh`) can also prepare the local development environment by installing dependencies and creating necessary configuration files.

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

### Backend Engine
- **FastAPI** - Web framework for all services
- **Poetry** - Dependency management
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Patient Data Service
- **Epic FHIR API** - Patient data integration
- **REST APIs** - Service communication

### Medical Imaging Service
- **MONAI** - Medical AI framework
- **PyTorch** - Deep learning framework
- **DICOM** - Medical image formats

### Biomedical LLM Service
- **Transformers** - HuggingFace transformers library
- **MONAI** - Multimodal medical AI
- **NumPy/SciPy** - Scientific computing

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

Environment files are automatically created by the setup script. You can customize them:

```bash
# Backend services
backend/engine/.env
backend/patient_data/.env
backend/medical_imaging/.env
backend/biomedical_llm/.env

# Frontend
frontend/.env
```

Example configuration:
```bash
# backend/engine/.env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
SERVICE_PORT=8000
SECRET_KEY=your-production-secret-key
JWT_SECRET=your-jwt-secret
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

## 🛠️ Setup Script Details

The `setup.sh` script provides automated environment setup:

**What it does:**
- Checks prerequisites (Docker, Node.js, Python, Poetry)
- Fixes common Docker issues and cleans build cache
- Creates environment files for all services with default configurations
- Sets up backend dependencies using Poetry
- Sets up frontend dependencies using npm
- Validates project structure
- Optionally tests Docker builds

**Usage:**
```bash
./setup.sh                    # Run full setup
./setup.sh --help            # Show help (coming soon)
```

**Manual environment file creation:**
If you prefer to create environment files manually, refer to the templates created by the setup script or see the individual service documentation.

## 📚 Documentation

- [Frontend README](frontend/README.md) - Frontend development guide
- [Backend Service READMEs](backend/) - Individual service documentation
- Run `make help` for available Docker commands

## 📄 License

This project is for educational and research purposes.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section in the Docker README
2. Review service-specific documentation
3. Check service logs: `make logs`
4. Verify service health: `make health`
