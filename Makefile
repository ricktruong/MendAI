.PHONY: help build up down restart logs clean dev dev-build dev-up dev-down dev-restart dev-logs backend-build backend-up backend-down status health

# Default target
help:
	@echo "MendAI Docker Management Commands"
	@echo ""
	@echo "Development Commands (Hot Reload):"
	@echo "  dev       - Start all services in development mode with hot reload"
	@echo "  dev-build - Build all Docker images for development"
	@echo "  dev-up    - Start all services in development mode (detached)"
	@echo "  dev-down  - Stop all development services"
	@echo "  dev-restart - Restart all development services"
	@echo "  dev-logs  - View logs from development services"
	@echo ""
	@echo "Production Commands:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - View logs from all services"
	@echo "  clean     - Remove all containers, images, and volumes"
	@echo ""
	@echo "Backend Only Commands:"
	@echo "  backend-build - Build only backend services"
	@echo "  backend-up    - Start only backend services"
	@echo "  backend-down  - Stop only backend services"
	@echo ""
	@echo "Utility Commands:"
	@echo "  status    - Show status of all services"
	@echo "  health    - Check health of all services"

# Development commands (with hot reload)
dev:
	docker compose -f docker-compose.dev.yml up --build

dev-build:
	docker compose -f docker-compose.dev.yml build

dev-up:
	docker compose -f docker-compose.dev.yml up -d

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-restart:
	docker compose -f docker-compose.dev.yml restart

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

# Production commands
build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

clean:
	docker compose down -v --rmi all --remove-orphans

# Backend only commands
backend-build:
	docker compose build engine patient_data medical_imaging biomedical_llm

backend-up:
	docker compose up -d engine patient_data medical_imaging biomedical_llm

backend-down:
	docker compose stop engine patient_data medical_imaging biomedical_llm

# Utility commands
status:
	docker compose ps

health:
	@echo "Checking service health..."
	@curl -s http://localhost:3000/health || echo "Frontend: ❌"
	@curl -s http://localhost:8000/health || echo "Engine: ❌"
	@curl -s http://localhost:8001/health || echo "Patient Data: ❌"
	@curl -s http://localhost:8002/health || echo "Medical Imaging: ❌"
	@curl -s http://localhost:8003/health || echo "Biomedical LLM: ❌" 