# Docker Setup Guide

This project supports multiple Docker configurations for different environments and hardware capabilities.

## Quick Start

### Development (CPU-only)
```bash
# Start all services with CPU-only containers
docker-compose up

# Or build and start
docker-compose up --build
```

### Production with GPU Support
```bash
# Start all services with GPU-enabled containers for medical_imaging and biomedical_llm
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up

# Or build and start
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### Production (CPU-only)
```bash
# Start all services with production CPU containers
docker-compose up

# Or build and start
docker-compose up --build
```

## Configuration Files

### Base Configuration
- `docker-compose.yml` - Main configuration with all services

### Override Files
- `docker-compose.gpu.yml` - GPU-enabled overrides for medical_imaging and biomedical_llm

## Service Architecture

### Frontend Service
- **Build Context**: `./frontend`
- **Dockerfile**: `frontend/Dockerfile`
- **Port**: 3000
- **Technology**: React/TypeScript

### Backend Services
All backend services share the build context `./backend` and the `common/` package.

#### Engine Service
- **Dockerfile**: `backend/engine/Dockerfile`
- **Port**: 8000
- **Technology**: FastAPI/Python

#### Patient Data Service
- **Dockerfile**: `backend/patient_data/Dockerfile`
- **Port**: 8001
- **Technology**: FastAPI/Python

#### Medical Imaging Service
- **CPU Dockerfile**: `backend/medical_imaging/Dockerfile`
- **GPU Dockerfile**: `backend/medical_imaging/Dockerfile.gpu`
- **Port**: 8002
- **Technology**: FastAPI/Python + GPU libraries

#### Biomedical LLM Service
- **CPU Dockerfile**: `backend/biomedical_llm/Dockerfile`
- **GPU Dockerfile**: `backend/biomedical_llm/Dockerfile.gpu`
- **Port**: 8003
- **Technology**: FastAPI/Python + GPU libraries

## GPU Requirements

### Prerequisites
1. **NVIDIA GPU** with CUDA support
2. **NVIDIA Docker Runtime** installed
3. **Docker Compose** version 3.8+

### Installation
```bash
# Install NVIDIA Docker Runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Verification
```bash
# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

## Environment Variables

### Development
Set in `docker-compose.dev.yml`:
- `ENVIRONMENT=development`
- `DEBUG=true`
- `NODE_ENV=development`

### Production
Set in individual service `.env` files:
- `ENVIRONMENT=production`
- `DEBUG=false`

## Build Commands

### Build All Services
```bash
# CPU-only
docker-compose build

# GPU-enabled
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build
```

### Build Specific Service
```bash
# CPU version (default)
docker-compose build medical_imaging

# GPU version
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build medical_imaging
```

## Troubleshooting

### GPU Issues
1. **Check NVIDIA Docker installation**:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
   ```

2. **Verify Docker Compose version**:
   ```bash
   docker-compose version
   ```

3. **Check GPU availability**:
   ```bash
   nvidia-smi
   ```

### Build Issues
1. **Clear Docker cache**:
   ```bash
   docker system prune -a
   ```

2. **Rebuild without cache**:
   ```bash
   docker-compose build --no-cache
   ```

### Port Conflicts
If ports are already in use, modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "127.0.0.1:8002:8002"  # Change 8002 to available port
```

## Performance Optimization

### GPU Services
- Use `docker-compose.gpu.yml` for production GPU workloads
- Monitor GPU memory usage with `nvidia-smi`
- Consider using GPU memory limits if needed

### CPU Services
- Use base `docker-compose.yml` for both development and production CPU workloads

## Security Considerations

### Non-root Users
All containers run as non-root user `app` for security.

### Environment Variables
- Never commit `.env` files to version control
- Use Docker secrets for sensitive data in production

### Network Isolation
All services run on the `mendai-network` bridge network for isolation.

## Monitoring

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs medical_imaging

# Follow logs in real-time
docker-compose logs -f
```

### Resource Usage
```bash
# Check container resource usage
docker stats

# Check GPU usage (if using GPU)
nvidia-smi
```
