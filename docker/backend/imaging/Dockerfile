# Use shared Python GPU base image
FROM mendai/python-gpu-base:latest

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies (production only)
RUN poetry install --no-dev --no-interaction --no-ansi

# Install PyTorch and CUDA support if not on Jetson
RUN if [ ! -f /etc/nv_tegra_release ] && [ "$(uname -m)" != "aarch64" ]; then \
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu; \
    fi

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"] 