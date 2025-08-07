.PHONY: help build up down restart logs clean dev-build dev-up dev-down dev-logs

# Default target
help:
	@echo "MendAI Docker Management Commands"
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

# Production commands
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

# Backend only commands
backend-build:
	cd backend && docker-compose build

backend-up:
	cd backend && docker-compose up -d

backend-down:
	cd backend && docker-compose down

# Utility commands
status:
	docker-compose ps

health:
	@echo "Checking service health..."
	@curl -s http://localhost:3000/health || echo "Frontend: ❌"
	@curl -s http://localhost:8000/health || echo "Engine: ❌"
	@curl -s http://localhost:8001/health || echo "Patient Data: ❌"
	@curl -s http://localhost:8002/health || echo "Imaging: ❌"
	@curl -s http://localhost:8003/health || echo "Biomedical LLM: ❌" 