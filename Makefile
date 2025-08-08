.PHONY: help build up down restart logs clean gpu-build gpu-up gpu-down gpu-logs backend-build backend-up backend-down status health

# Default target
help:
	@echo "MendAI Docker Management Commands"
	@echo ""
	@echo "CPU Commands (Default):"
	@echo "  build     - Build all Docker images (CPU-only)"
	@echo "  up        - Start all services (CPU-only)"
	@echo "  down      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - View logs from all services"
	@echo "  clean     - Remove all containers, images, and volumes"
	@echo ""
	@echo "GPU Commands:"
	@echo "  gpu-build - Build all Docker images with GPU support"
	@echo "  gpu-up    - Start all services with GPU support"
	@echo "  gpu-down  - Stop GPU services"
	@echo "  gpu-logs  - View logs from GPU services"
	@echo ""
	@echo "Backend Only Commands:"
	@echo "  backend-build - Build only backend services"
	@echo "  backend-up    - Start only backend services"
	@echo "  backend-down  - Stop only backend services"
	@echo ""
	@echo "Utility Commands:"
	@echo "  status    - Show status of all services"
	@echo "  health    - Check health of all services"

# CPU commands (default)
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi all --remove-orphans

# GPU commands
gpu-build:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build

gpu-up:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

gpu-down:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml down

gpu-logs:
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml logs -f

# Backend only commands
backend-build:
	docker-compose build engine patient_data medical_imaging biomedical_llm

backend-up:
	docker-compose up -d engine patient_data medical_imaging biomedical_llm

backend-down:
	docker-compose stop engine patient_data medical_imaging biomedical_llm

# Utility commands
status:
	docker-compose ps

health:
	@echo "Checking service health..."
	@curl -s http://localhost:3000/health || echo "Frontend: ❌"
	@curl -s http://localhost:8000/health || echo "Engine: ❌"
	@curl -s http://localhost:8001/health || echo "Patient Data: ❌"
	@curl -s http://localhost:8002/health || echo "Medical Imaging: ❌"
	@curl -s http://localhost:8003/health || echo "Biomedical LLM: ❌" 