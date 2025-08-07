# Backend Engine

This is the main backend engine for the integrated medical workflow solution. It handles routing, API aggregation, and communication with microservices.

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run the service:
   ```bash
   poetry run uvicorn engine.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables
- You can use a `.env` file to set environment variables (e.g., `BACKEND_ENGINE_PORT`). 