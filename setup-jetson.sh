#!/bin/bash

# MendAI Jetson AGX Orin Setup Script
# This script sets up the Docker environment for running MendAI on NVIDIA Jetson AGX Orin

set -e

echo "🚀 Setting up MendAI on NVIDIA Jetson AGX Orin..."

# Check if running on Jetson
# if ! command -v nvidia-smi &> /dev/null; then
    # echo "❌ Error: nvidia-smi not found. This script is designed for NVIDIA Jetson devices."
    # exit 1
# fi

# Check JetPack version
JETPACK_VERSION=$(cat /etc/nv_tegra_release | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "📋 Detected JetPack version: $JETPACK_VERSION"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found. Please install Docker first."
    echo "📖 Install Docker: https://docs.docker.com/engine/install/ubuntu/"
    exit 1
fi

# Check Docker Compose installation
# if ! command -v docker compose &> /dev/null; then
#     echo "❌ Error: Docker Compose not found. Please install Docker Compose first."
#     echo "📖 Install Docker Compose: https://docs.docker.com/compose/install/"
#     exit 1
# fi

# Check NVIDIA Container Runtime
if ! docker info | grep -q "nvidia"; then
    echo "⚠️  Warning: NVIDIA Container Runtime not detected."
    echo "📖 Install NVIDIA Container Runtime: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    echo "💡 This is required for GPU access in containers."
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# MendAI Environment Configuration
# Generated on $(date)

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000

# Backend Services Configuration
PATIENT_DATA_SERVICE_URL=http://patient-data:8001
IMAGING_SERVICE_URL=http://imaging:8002
BIOMEDICAL_LLM_SERVICE_URL=http://biomedical-llm:8003

# GPU Configuration
CUDA_VISIBLE_DEVICES=0

# Logging
LOG_LEVEL=INFO
EOF
    echo "✅ Created .env file"
fi

# Create poetry.lock files if they don't exist
echo "📦 Checking Poetry dependencies..."
for service in backend/engine backend/patient-data backend/imaging backend/biomedical-llm; do
    if [ -f "$service/pyproject.toml" ] && [ ! -f "$service/poetry.lock" ]; then
        echo "🔧 Generating poetry.lock for $service..."
        cd "$service"
        poetry lock --no-update
        cd - > /dev/null
    fi
done

# Build base images and services
echo "🏗️  Building base images..."
./docker/build-base-images.sh

echo "🏗️  Building Docker images..."
docker-compose build

echo "🚀 Starting MendAI services..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "🎉 MendAI setup complete!"
echo ""
echo "📋 Service URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend Engine: http://localhost:8000"
echo "   Patient Data: http://localhost:8001"
echo "   Imaging: http://localhost:8002"
echo "   Biomedical LLM: http://localhost:8003"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update services: docker-compose pull && docker-compose up -d"
echo ""
echo "📖 For more information, see README.md" 