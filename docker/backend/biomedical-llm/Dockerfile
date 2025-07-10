# Use shared Python GPU base image
FROM mendai/python-gpu-base:latest

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies (production only)
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"] 