# MendAI: Your Agentic AI Healthcare Assistant

A comprehensive healthcare application that enables healthcare professionals to access patient data, process medical scans, analyze laboratory results, and receive AI-assisted patient prognosis through a seamless, integrated medical workflow platform.

## Architecture

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

## Project Structure

```
Project/
├── frontend/                # React + Vite + TypeScript
├── backend/
│   ├── engine/              # Main backend engine (API gateway, routing)
│   ├── patient-data/        # Patient data service (Epic FHIR integration)
│   ├── imaging/             # Medical imaging service (MONAI)
│   └── biomedical-llm/      # LLM service (MONAI + Transformers)
├── common/                  # Common code, types, utilities
```

## Quick Start

### Prerequisites
- Node.js (for frontend)
- Python 3.9+ (for backend services)
- Poetry (for Python dependency management)

### Frontend Setup
Follow frontend/README.md for Front-end setup

### Backend Services Setup

#### Backend Engine
Follow backend/engine/README.md for Backend Engine setup

#### Patient Data Service
Follow backend/patient-data/README.md for Patient Data Service setup

#### Medical Imaging Service
Follow backend/imaging/README.md for Medical Imaging Service setup

#### Biomedical LLM Service
Follow backend/biomedical-llm/README.md for Biomedical LLM Service setup

## 🔧 Services

### Backend Engine
- API gateway and routing
- Authentication and authorization
- Request aggregation
- Service orchestration

### Patient Data Service
- Epic FHIR API integration
- Patient data storage and retrieval
- Biometric data management
- Medical history tracking

### Medical Imaging Service
- DICOM file processing
- Medical image segmentation
- Disease detection and classification
- MONAI model integration

### Biomedical LLM Service
- Multimodal image-text processing
- Biomedical chatbot functionality
- AI-assisted patient prognosis
- Clinical text analysis

## Tech Stack

Current tech stack

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling (planned)

### Backend
- **FastAPI** - Web framework for all services
- **Poetry** - Dependency management
- **Uvicorn** - ASGI server

### Medical Imaging
- **MONAI** - Medical AI framework
- **PyTorch** - Deep learning framework

### AI/ML
- **Transformers** - HuggingFace transformers library
- **MONAI** - Multimodal medical AI

### Data Integration
- **Epic FHIR API** - Patient data integration
- **DICOM** - Medical image formats


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and research purposes.
