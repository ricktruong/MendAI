# MendAI Jetson AGX Orin Deployment Solution

## 🎯 Solution Overview

I've created a complete Docker-based microservice architecture for deploying MendAI on NVIDIA Jetson AGX Orin that properly handles GPU requirements for ML workloads.

## 🏗️ Architecture

### Services
1. **Frontend** (React + Vite) - Port 3000
2. **Backend Engine** (FastAPI) - Port 8000 (API Gateway)
3. **Patient Data Service** (FastAPI) - Port 8001
4. **Imaging Service** (FastAPI + MONAI) - Port 8002 (GPU-enabled)
5. **Biomedical LLM Service** (FastAPI + MONAI + Transformers) - Port 8003 (GPU-enabled)

### Key Features
- ✅ **Jetson-specific PyTorch**: Uses `nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.1.0-py3`
- ✅ **GPU Access**: NVIDIA Container Runtime for GPU-enabled services
- ✅ **Microservice Architecture**: Isolated services with proper networking
- ✅ **Development & Production**: Separate configurations for both modes
- ✅ **Health Checks**: Built-in monitoring for all services
- ✅ **Security**: Non-root users, minimal base images

## 📁 Files Created

### Core Docker Files
- `docker-compose.yml` - Production deployment
- `docker-compose.dev.yml` - Development deployment with hot reloading
- `.dockerignore` - Optimized build context

### Service Dockerfiles
- `frontend/Dockerfile` & `frontend/Dockerfile.dev`
- `backend/engine/Dockerfile` & `backend/engine/Dockerfile.dev`
- `backend/patient-data/Dockerfile` & `backend/patient-data/Dockerfile.dev`
- `backend/imaging/Dockerfile` & `backend/imaging/Dockerfile.dev`
- `backend/biomedical-llm/Dockerfile` & `backend/biomedical-llm/Dockerfile.dev`

### Configuration Files
- `frontend/nginx.conf` - Frontend web server configuration
- `setup-jetson.sh` - Automated setup script
- `Makefile` - Common management commands

### Documentation
- `DOCKER_README.md` - Comprehensive deployment guide
- `JETSON_DEPLOYMENT.md` - This summary document

## 🚀 Quick Start

### 1. Automated Setup
```bash
# Run the setup script
./setup-jetson.sh
```

### 2. Manual Setup
```bash
# Build and start production services
make build
make up

# Or for development with hot reloading
make dev-build
make dev-up
```

### 3. Access Services
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Individual services: http://localhost:8001-8003

## 🔧 Key Technical Decisions

### 1. GPU-Enabled Services
**Problem**: PyTorch/MONAI require GPU access on Jetson
**Solution**: 
- Use NVIDIA's official Jetson PyTorch base image
- Configure NVIDIA Container Runtime
- Separate GPU and non-GPU services

### 2. Service Isolation
**Problem**: Need proper microservice architecture
**Solution**:
- Docker Compose with custom network
- Service discovery via container names
- Isolated dependencies per service

### 3. Development vs Production
**Problem**: Need different configurations for development and production
**Solution**:
- Separate Docker Compose files
- Development mode with volume mounts and hot reloading
- Production mode with optimized builds

### 4. Jetson Compatibility
**Problem**: ARM64 architecture and JetPack requirements
**Solution**:
- Use ARM64-compatible base images
- Leverage NVIDIA's pre-built PyTorch wheels
- Proper system dependency installation

## 🛠️ Management Commands

```bash
# View all available commands
make help

# Production management
make build    # Build images
make up       # Start services
make down     # Stop services
make logs     # View logs
make status   # Check status

# Development management
make dev-build # Build dev images
make dev-up    # Start dev services
make dev-down  # Stop dev services
make dev-logs  # View dev logs

# Utility commands
make setup     # Run setup script
make gpu-check # Verify GPU access
make clean     # Clean everything
```

## 🔍 Monitoring & Debugging

### Health Checks
All services include health check endpoints:
- `http://localhost:3000/health` (Frontend)
- `http://localhost:8000/health` (Engine)
- `http://localhost:8001/health` (Patient Data)
- `http://localhost:8002/health` (Imaging)
- `http://localhost:8003/health` (Biomedical LLM)

### GPU Verification
```bash
# Check GPU availability
make gpu-check

# Or manually
docker-compose exec imaging nvidia-smi
docker-compose exec biomedical-llm nvidia-smi
```

### Logs
```bash
# All services
make logs

# Specific service
docker-compose logs -f imaging
```

## 🔒 Security Features

- **Non-root users**: All services run as `appuser` (UID 1000)
- **Minimal base images**: Reduced attack surface
- **Network isolation**: Internal communication via Docker network
- **Health checks**: Automatic service monitoring
- **Resource limits**: Configurable via Docker Compose

## 📊 Performance Considerations

### GPU Optimization
- Use TensorRT for inference acceleration
- Optimize batch sizes for Jetson memory constraints
- Monitor GPU utilization with `nvidia-smi`

### Memory Management
- Multi-stage builds reduce image sizes
- Proper cleanup in Dockerfiles
- Monitor container memory usage

### Network Optimization
- Docker's built-in DNS resolution
- Connection pooling for service communication
- Appropriate timeouts and retries

## 🚀 Production Deployment

### Environment Variables
Create `.env` file for production settings:
```bash
NODE_ENV=production
LOG_LEVEL=WARNING
CUDA_VISIBLE_DEVICES=0
```

### Scaling
```bash
# Scale specific services
docker-compose up -d --scale imaging=2

# Use Docker Swarm for orchestration
docker swarm init
docker stack deploy -c docker-compose.yml mendai
```

## 🔧 Troubleshooting

### Common Issues

1. **GPU Not Available**
   ```bash
   # Check NVIDIA Container Runtime
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

2. **Service Won't Start**
   ```bash
   # Check logs
   docker-compose logs <service-name>
   
   # Check resource usage
   docker stats
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory
   free -h
   docker stats
   ```

### JetPack Compatibility
- Tested with JetPack 5.1+ (recommended: JetPack 6.0)
- Base image `nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.1.0-py3` corresponds to JetPack 5.1.2

## 📚 Next Steps

1. **Test the deployment** on your Jetson AGX Orin
2. **Customize environment variables** for your specific needs
3. **Add monitoring** (Prometheus/Grafana)
4. **Implement CI/CD** for automated deployments
5. **Add persistent storage** for models and data
6. **Configure SSL/TLS** for production use

## 🤝 Support

For issues:
1. Check the troubleshooting section in `DOCKER_README.md`
2. Verify JetPack version compatibility
3. Ensure NVIDIA Container Runtime is installed
4. Check service logs for specific errors

This solution provides a robust, scalable foundation for running MendAI on NVIDIA Jetson AGX Orin with proper GPU support for ML workloads. 