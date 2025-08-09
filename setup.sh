#!/bin/bash

# MendAI Setup Script
# This script sets up the complete MendAI development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker Desktop first."
        log_info "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command_exists docker compose && ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not installed or accessible."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    # Check Node.js (for frontend development)
    if ! command_exists node; then
        log_warning "Node.js is not installed. Frontend development will require Node.js 18+."
        log_info "Download from: https://nodejs.org/"
    else
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -lt 18 ]; then
            log_warning "Node.js version is $NODE_VERSION. Recommended version is 18+."
        fi
    fi
    
    # Check Python (required for Poetry and local development)
    if ! command_exists python3; then
        log_warning "Python 3 is not installed. Backend development requires Python 3.9+."
        log_info "Download from: https://www.python.org/downloads/"
    else
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
            log_warning "Python version is $PYTHON_VERSION. Required version is 3.9+."
            log_info "Please upgrade Python to 3.9 or higher"
        else
            log_info "Python version $PYTHON_VERSION detected ✓"
        fi
    fi
    
    # Check Poetry (for local development)
    if ! command_exists poetry; then
        log_warning "Poetry is not installed. Backend local development will require Poetry."
        log_info "Install with: curl -sSL https://install.python-poetry.org | python3 -"
    else
        POETRY_VERSION=$(poetry --version 2>/dev/null | cut -d' ' -f3 || echo "unknown")
        log_info "Poetry version $POETRY_VERSION detected ✓"
    fi
    
    log_success "Prerequisites check completed"
}

# Fix Docker issues
fix_docker_issues() {
    log_info "Fixing common Docker issues..."
    
    # Clean up Docker system
    log_info "Cleaning Docker system..."
    docker system prune -f >/dev/null 2>&1 || true
    
    # Try to clean build cache
    log_info "Cleaning Docker build cache..."
    docker builder prune -f >/dev/null 2>&1 || true
    
    # Restart Docker BuildKit
    log_info "Restarting Docker BuildKit..."
    docker buildx rm --all-inactive >/dev/null 2>&1 || true
    
    log_success "Docker cleanup completed"
}

# Create environment files
create_environment_files() {
    log_info "Creating environment file templates..."
    
    # Backend service environment files
    BACKEND_SERVICES=("engine" "patient_data" "medical_imaging" "biomedical_llm")
    
    for service in "${BACKEND_SERVICES[@]}"; do
        env_file="backend/${service}/.env"
        if [ ! -f "$env_file" ]; then
            log_info "Creating $env_file"
            
            # Assign service-specific port
            case "$service" in
                "engine") service_port="8000" ;;
                "patient_data") service_port="8001" ;;
                "medical_imaging") service_port="8002" ;;
                "biomedical_llm") service_port="8003" ;;
                *) service_port="8000" ;;
            esac
            
            cat > "$env_file" << EOF
# ${service} Service Environment Variables
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Service Configuration
SERVICE_NAME=${service}
SERVICE_PORT=${service_port}
SERVICE_HOST=0.0.0.0

# Database Configuration (if needed)
# DATABASE_URL=postgresql://user:password@localhost:5432/mendai_${service}

# External APIs (if needed)
# API_KEY=your_api_key_here
# API_URL=https://api.example.com

# Security
# SECRET_KEY=your_secret_key_here
# JWT_SECRET=your_jwt_secret_here

# Add service-specific environment variables below
EOF
        else
            log_info "$env_file already exists, skipping..."
        fi
    done
    
    # Frontend environment file
    frontend_env="frontend/.env"
    if [ ! -f "$frontend_env" ]; then
        log_info "Creating $frontend_env"
        cat > "$frontend_env" << EOF
# Frontend Environment Variables
NODE_ENV=development
VITE_APP_NAME=MendAI

# Backend API URLs
VITE_API_BASE_URL=http://localhost:8000
VITE_ENGINE_API_URL=http://localhost:8000
VITE_PATIENT_DATA_API_URL=http://localhost:8001
VITE_MEDICAL_IMAGING_API_URL=http://localhost:8002
VITE_BIOMEDICAL_LLM_API_URL=http://localhost:8003

# Feature Flags
VITE_ENABLE_GPU_FEATURES=false
VITE_ENABLE_DEBUG_MODE=true

# Add frontend-specific environment variables below
EOF
    else
        log_info "$frontend_env already exists, skipping..."
    fi
    
    log_success "Environment files created"
}

# Setup backend services
setup_backend() {
    log_info "Setting up backend services..."
    
    BACKEND_SERVICES=("common" "engine" "patient_data" "medical_imaging" "biomedical_llm")
    
    for service in "${BACKEND_SERVICES[@]}"; do
        log_info "Setting up backend/${service}..."
        
        cd "backend/${service}"
        
        # Check if poetry.lock exists and is up to date
        if [ ! -f "poetry.lock" ] || [ "pyproject.toml" -nt "poetry.lock" ]; then
            log_info "Running poetry lock for ${service}..."
            if command_exists poetry; then
                poetry lock
            else
                log_warning "Poetry not found, skipping lock for ${service}"
            fi
        else
            log_info "poetry.lock is up to date for ${service}"
        fi
        
        cd - >/dev/null
    done
    
    log_success "Backend setup completed"
}

# Setup frontend
setup_frontend() {
    log_info "Setting up frontend..."
    
    cd frontend
    
    # Check if package-lock.json exists and node_modules is up to date
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
        if command_exists npm; then
            log_info "Installing frontend dependencies..."
            npm ci >/dev/null 2>&1 || npm install >/dev/null 2>&1
        else
            log_warning "npm not found, skipping frontend dependency installation"
        fi
    else
        log_info "Frontend dependencies are up to date"
    fi
    
    cd - >/dev/null
    
    log_success "Frontend setup completed"
}

# Validate setup
validate_setup() {
    log_info "Validating setup..."
    
    # Check if all required files exist
    REQUIRED_FILES=(
        "docker-compose.yml"
        "docker-compose.gpu.yml"
        "Makefile"
        "backend/.dockerignore"
        "frontend/.dockerignore"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file missing: $file"
            exit 1
        fi
    done
    
    # Check if backend services exist
    BACKEND_SERVICES=("engine" "patient_data" "medical_imaging" "biomedical_llm" "common")
    for service in "${BACKEND_SERVICES[@]}"; do
        if [ ! -d "backend/${service}" ]; then
            log_error "Backend service missing: backend/${service}"
            exit 1
        fi
        
        if [ ! -f "backend/${service}/pyproject.toml" ]; then
            log_error "pyproject.toml missing for: backend/${service}"
            exit 1
        fi
    done
    
    # Check if frontend exists
    if [ ! -d "frontend" ] || [ ! -f "frontend/package.json" ]; then
        log_error "Frontend configuration missing"
        exit 1
    fi
    
    log_success "Setup validation completed"
}

# Test Docker build
test_docker_build() {
    log_info "Testing Docker build (this may take a few minutes)..."
    
    # Test building one service first
    log_info "Testing frontend build..."
    if docker compose build frontend >/dev/null 2>&1; then
        log_success "Frontend build test passed"
    else
        log_error "Frontend build test failed"
        log_info "You can try running 'make build' manually to see detailed errors"
        return 1
    fi
    
    log_info "Testing backend build..."
    if docker compose build engine >/dev/null 2>&1; then
        log_success "Backend build test passed"
    else
        log_error "Backend build test failed"
        log_info "You can try running 'make build' manually to see detailed errors"
        return 1
    fi
    
    log_success "Docker build tests completed"
}

# Main setup function
main() {
    echo "======================================"
    echo "      MendAI Setup Script v1.0       "
    echo "======================================"
    echo ""
    
    # Ensure we're in the project root
    if [ ! -f "docker-compose.yml" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        log_error "Please run this script from the MendAI project root directory"
        exit 1
    fi
    
    log_info "Starting MendAI setup..."
    
    # Run setup steps
    check_prerequisites
    fix_docker_issues
    create_environment_files
    setup_backend
    setup_frontend
    validate_setup
    
    # Optional: test Docker build
    read -p "Do you want to test the Docker build? This may take a few minutes. (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_docker_build
    fi
    
    echo ""
    echo "======================================"
    log_success "MendAI setup completed successfully!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Review and customize the .env files in each service directory"
    echo "2. Run 'make build' to build all Docker images"
    echo "3. Run 'make up' to start all services"
    echo "4. Access the application:"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:8000"
    echo ""
    echo "For GPU support:"
    echo "1. Install NVIDIA Docker Runtime"
    echo "2. Run 'make gpu-build && make gpu-up'"
    echo ""
    echo "For more information, see:"
    echo "- README.md"
    echo "- DOCKER_SETUP.md"
    echo "- Run 'make help' for available commands"
    echo ""
}

# Run main function
main "$@"