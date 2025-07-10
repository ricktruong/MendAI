# Shared Python base image for non-GPU services
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
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