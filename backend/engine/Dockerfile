# Shared Python base image for non-GPU services
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create a non-root user
RUN useradd -m app

# Create log directory in container
RUN mkdir -p /log && chown app /log

# Install Poetry
RUN python -m pip install --upgrade pip poetry --no-cache-dir

# Copy poetry files
COPY engine/pyproject.toml engine/poetry.lock ./

# Copy common package into container
COPY common/ ../common/

# Configure Poetry to not create virtual environment (since we're in a container)
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-interaction --no-ansi

# Copy Backend Engine code into container
COPY --chown=app engine/ ./

USER app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "engine.main:app", "--host", "0.0.0.0", "--port", "8000"]