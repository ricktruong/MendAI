# Shared Python GPU base image for GPU-enabled services (Jetson)
FROM nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.1.0-py3

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry to not create virtual environment (since we're in a container)
RUN poetry config virtualenvs.create false

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Change ownership to appuser
RUN chown -R appuser:appuser /app

USER appuser 