# MendAI Docker Setup for NVIDIA Jetson AGX Orin

This guide provides instructions for deploying MendAI on NVIDIA Jetson AGX Orin using Docker containers with proper GPU support for ML workloads.

## 🎯 Overview

MendAI is deployed as a microservice architecture with the following services:

- **Frontend** (React + Vite) - Port 3000
- **Backend Engine** (FastAPI) - Port 8000
- **Patient Data Service** (FastAPI) - Port 8001
- **Imaging Service** (FastAPI + MONAI) - Port 8002 (GPU-enabled)
- **Biomedical LLM Service** (FastAPI + MONAI + Transformers) - Port 8003 (GPU-enabled)

## 🚀 Quick Start

### Prerequisites

1. **NVIDIA Jetson AGX Orin** with JetPack 5.1+ (recommended: JetPack 6.0)
2. **Docker** installed
3. **Docker Compose** installed
4. **NVIDIA Container Runtime** installed

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd MendAI
   ```

2. **Run the setup script:**
   ```bash
   ./setup-jetson.sh
   ```

   This script will:
   - Check your Jetson environment
   - Create necessary configuration files
   - Build Docker images
   - Start all services

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🔧 Manual Setup

If you prefer to set up manually or need to customize the deployment:

### 1. Install Prerequisites

#### Docker Installation
```bash
# Update package list
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

#### Docker Compose Installation
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### NVIDIA Container Runtime
```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker daemon
sudo systemctl restart docker
```

### 2. Build and Deploy

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🏗️ Architecture Details

### GPU-Enabled Services

The **Imaging Service** and **Biomedical LLM Service** are configured to use NVIDIA GPU:

- **Base Image**: `nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.1.0-py3`
- **GPU Access**: Via NVIDIA Container Runtime
- **PyTorch**: Pre-built for Jetson (ARM64)
- **MONAI**: Installed with GPU support

### Service Dependencies

```
Frontend → Backend Engine → [Patient Data, Imaging, Biomedical LLM]
```

### Network Configuration

- **Internal Network**: `mendai-network` (bridge)
- **Service Discovery**: Via Docker Compose service names
- **Port Mapping**: External ports mapped to container ports

## 🔍 Monitoring and Debugging

### Service Health Checks

All services include health check endpoints:
- Frontend: `http://localhost:3000/health`
- Backend Engine: `http://localhost:8000/health`
- Patient Data: `http://localhost:8001/health`
- Imaging: `http://localhost:8002/health`
- Biomedical LLM: `http://localhost:8003/health`

### Useful Commands

```bash
# View all container logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f imaging

# Check GPU usage
nvidia-smi

# Access container shell
docker-compose exec imaging bash

# Restart specific service
docker-compose restart imaging

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Troubleshooting

#### GPU Not Available
```bash
# Check NVIDIA Container Runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Verify GPU access in container
docker-compose exec imaging nvidia-smi
```

#### Service Won't Start
```bash
# Check service logs
docker-compose logs <service-name>

# Check resource usage
docker stats

# Verify port availability
netstat -tulpn | grep :8000
```

#### Memory Issues
```bash
# Monitor memory usage
free -h
docker stats

# Adjust Docker memory limits in docker-compose.yml
```

## 🔒 Security Considerations

### Container Security
- All services run as non-root users
- Minimal base images used
- Health checks implemented
- Resource limits configured

### Network Security
- Internal service communication via Docker network
- External access only through defined ports
- No direct database exposure

### Environment Variables
- Sensitive data stored in `.env` file
- `.env` file should not be committed to version control
- Use Docker secrets for production deployments

## 📊 Performance Optimization

### GPU Optimization
- Use TensorRT for inference acceleration
- Optimize batch sizes for Jetson memory
- Monitor GPU utilization with `nvidia-smi`

### Memory Optimization
- Use multi-stage builds to reduce image size
- Implement proper cleanup in Dockerfiles
- Monitor container memory usage

### Network Optimization
- Use Docker's built-in DNS resolution
- Implement connection pooling
- Use appropriate timeouts

## 🚀 Production Deployment

### Environment Variables
Create a `.env` file with production settings:
```bash
# Production Configuration
NODE_ENV=production
LOG_LEVEL=WARNING
CUDA_VISIBLE_DEVICES=0

# Database Configuration (if applicable)
DATABASE_URL=your_database_url

# API Keys and Secrets
API_KEY=your_api_key
```

### Scaling
```bash
# Scale specific services
docker-compose up -d --scale imaging=2

# Use Docker Swarm for orchestration
docker swarm init
docker stack deploy -c docker-compose.yml mendai
```

### Monitoring
- Implement Prometheus metrics
- Use Grafana for visualization
- Set up alerting for service health

## 📚 Additional Resources

- [NVIDIA Jetson Documentation](https://developer.nvidia.com/embedded/jetpack)
- [Docker Documentation](https://docs.docker.com/)
- [NVIDIA Container Runtime](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [MONAI Documentation](https://docs.monai.io/)
- [PyTorch Jetson](https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/70)

## 🤝 Support

For issues specific to Jetson deployment:
1. Check the troubleshooting section above
2. Verify your JetPack version compatibility
3. Ensure NVIDIA Container Runtime is properly installed
4. Check service logs for specific error messages

For general MendAI issues, please refer to the main README.md file. 