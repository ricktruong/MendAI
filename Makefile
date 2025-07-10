.PHONY: help build up down restart logs clean dev-build dev-up dev-down dev-logs

# Default target
help:
	@echo "MendAI Docker Management Commands"
	@echo ""
	@echo "Production Commands:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services in production mode"
	@echo "  down      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - View logs from all services"
	@echo "  clean     - Remove all containers, images, and volumes"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev-build - Build all Docker images for development"
	@echo "  dev-up    - Start all services in development mode"
	@echo "  dev-down  - Stop all development services"
	@echo "  dev-logs  - View logs from development services"
	@echo ""
	@echo "Utility Commands:"
	@echo "  setup     - Run the Jetson setup script"
	@echo "  status    - Show status of all services"
	@echo "  gpu-check - Check GPU availability in containers"

# Production commands
build-base:
	./docker/build-base-images.sh

build:
	./docker/build-base-images.sh
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

# Development commands
dev-build:
	./docker/build-base-images.sh
	docker-compose -f docker-compose.dev.yml build

dev-up:
	docker-compose -f docker-compose.dev.yml up -d

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Utility commands
setup:
	./setup-jetson.sh

status:
	docker-compose ps

gpu-check:
	@echo "Checking GPU availability..."
	@docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi || echo "GPU not available or NVIDIA Container Runtime not installed"
	@echo ""
	@echo "Checking GPU access in imaging service..."
	@docker-compose exec imaging nvidia-smi 2>/dev/null || echo "Imaging service not running or GPU not accessible"
	@echo ""
	@echo "Checking GPU access in biomedical-llm service..."
	@docker-compose exec biomedical-llm nvidia-smi 2>/dev/null || echo "Biomedical LLM service not running or GPU not accessible" 