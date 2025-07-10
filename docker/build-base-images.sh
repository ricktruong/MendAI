#!/bin/bash

# Build shared base images for MendAI
set -e

echo "🏗️  Building shared base images..."

# Build Python base image
echo "📦 Building Python base image..."
docker build -t mendai/python-base:latest -f docker/common/base-images/python-base.Dockerfile .

# TODO: Build Python GPU base image

# Build Python Jetson GPU base image
echo "📦 Building Python GPU base image..."
docker build -t mendai/python-gpu-base:latest -f docker/common/base-images/python-gpu-base.Dockerfile .

# Build Node.js base image
echo "📦 Building Node.js base image..."
docker build -t mendai/node-base:latest -f docker/common/base-images/node-base.Dockerfile .

echo "✅ All base images built successfully!"
echo ""
echo "📋 Available base images:"
echo "  - mendai/python-base:latest"
echo "  - mendai/python-gpu-base:latest"
echo "  - mendai/node-base:latest"