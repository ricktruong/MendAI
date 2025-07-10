# Docker Organization for MendAI

This directory contains all Docker-related files for the MendAI project, organized for better maintainability and reusability.

## 📁 Directory Structure

```
docker/
├── README.md                           # This file
├── build-base-images.sh                # Script to build shared base images
├── frontend/                           # Frontend service Dockerfiles
│   ├── Dockerfile                      # Production frontend
│   ├── Dockerfile.dev                  # Development frontend
│   └── nginx.conf                      # Nginx configuration
├── backend/                            # Backend services Dockerfiles
│   ├── engine/                         # Backend engine service
│   │   ├── Dockerfile                  # Production engine
│   │   └── Dockerfile.dev              # Development engine
│   ├── patient-data/                   # Patient data service
│   │   ├── Dockerfile                  # Production patient-data
│   │   └── Dockerfile.dev              # Development patient-data
│   ├── imaging/                        # Medical imaging service (GPU-enabled)
│   │   ├── Dockerfile                  # Production imaging
│   │   └── Dockerfile.dev              # Development imaging
│   └── biomedical-llm/                 # Biomedical LLM service (GPU-enabled)
│       ├── Dockerfile                  # Production biomedical-llm
│       └── Dockerfile.dev              # Development biomedical-llm
└── common/                             # Shared resources
    └── base-images/                    # Shared base images
        ├── python-base.Dockerfile      # Python base for non-GPU services
        ├── python-gpu-base.Dockerfile  # Python GPU base for GPU services
        └── node-base.Dockerfile        # Node.js base for frontend
```

## 🏗️ Architecture Overview

### Shared Base Images

We use shared base images to reduce duplication and ensure consistency:

1. **`mendai/python-base:latest`**
   - Based on `python:3.9-slim`
   - Includes Poetry, system dependencies, and non-root user
   - Used by: engine, patient-data services

2. **`mendai/python-gpu-base:latest`**
   - Based on `nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.1.0-py3`
   - Includes GPU support, Poetry, system dependencies, and non-root user
   - Used by: imaging, biomedical-llm services

3. **`mendai/node-base:latest`**
   - Based on `node:18-alpine`
   - Includes non-root user setup
   - Used by: frontend service

### Service Dockerfiles

Each service has two Dockerfiles:
- **`Dockerfile`**: Production optimized (multi-stage builds, no dev dependencies)
- **`Dockerfile.dev`**: Development optimized (single stage, includes dev dependencies, hot reloading)

## 🚀 Usage

### Building Base Images

```bash
# Build all base images
./docker/build-base-images.sh

# Or use Makefile
make build-base
```

### Building Services

```bash
# Production build (includes base images)
make build

# Development build (includes base images)
make dev-build
```

### Manual Building

```bash
# Build specific base image
docker build -t mendai/python-base:latest -f docker/common/base-images/python-base.Dockerfile .

# Build specific service
docker build -t mendai/engine:latest -f docker/backend/engine/Dockerfile ./backend/engine
```

## 🔧 Benefits of This Organization

### 1. **Reduced Duplication**
- Common setup (Poetry, users, dependencies) in base images
- Service Dockerfiles focus only on application-specific needs

### 2. **Faster Builds**
- Base images are built once and cached
- Service builds only need to install application dependencies

### 3. **Consistency**
- All services use the same base setup
- Easier to maintain security and dependency versions

### 4. **Maintainability**
- Centralized Dockerfile management
- Easy to update base images for all services
- Clear separation of concerns

### 5. **Flexibility**
- Easy to add new services
- Can customize base images for different needs
- Development and production configurations

## 📊 Build Performance

### Before (Scattered Dockerfiles)
- Each service: ~2-3 minutes build time
- Total build time: ~10-15 minutes
- Lots of duplicate work

### After (Shared Base Images)
- Base images: ~3-5 minutes (one-time)
- Each service: ~30-60 seconds
- Total build time: ~5-8 minutes
- Significant time savings on subsequent builds

## 🔄 Workflow

### Initial Setup
1. Build base images: `./docker/build-base-images.sh`
2. Build services: `make build` or `make dev-build`

### Development
1. Base images are cached, so builds are fast
2. Use `make dev-up` for development with hot reloading
3. Use `make up` for production-like testing

### Adding New Services
1. Create service directory in `docker/backend/`
2. Create `Dockerfile` and `Dockerfile.dev`
3. Use appropriate base image (`mendai/python-base` or `mendai/python-gpu-base`)
4. Update docker-compose files

## 🛠️ Customization

### Adding New Base Images
1. Create new Dockerfile in `docker/common/base-images/`
2. Update `build-base-images.sh` script
3. Update service Dockerfiles to use new base

### Modifying Base Images
1. Edit base image Dockerfile
2. Rebuild: `./docker/build-base-images.sh`
3. Rebuild services: `make build`

### Service-Specific Customization
- Add service-specific setup in service Dockerfiles
- Override base image behavior as needed
- Keep base images generic and reusable

## 🔍 Troubleshooting

### Base Image Issues
```bash
# Check if base images exist
docker images | grep mendai

# Rebuild base images
./docker/build-base-images.sh --no-cache
```

### Service Build Issues
```bash
# Build with verbose output
docker-compose build --progress=plain

# Build specific service
docker-compose build engine
```

### Cache Issues
```bash
# Clear Docker build cache
docker builder prune

# Rebuild everything
make clean
make build
```

## 📚 Best Practices

1. **Keep base images minimal**: Only include what's needed by multiple services
2. **Use specific tags**: Consider using versioned tags for base images
3. **Document changes**: Update this README when adding new services or base images
4. **Test thoroughly**: Ensure both development and production builds work
5. **Optimize layers**: Order Dockerfile instructions for better caching

## 🤝 Contributing

When adding new services or modifying Dockerfiles:

1. Follow the existing naming conventions
2. Use appropriate base images
3. Include both production and development versions
4. Update this documentation
5. Test builds locally before committing 