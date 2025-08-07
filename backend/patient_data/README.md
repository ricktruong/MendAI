# Patient Data Service

This service handles patient data management, including integration with Epic FHIR API and local data storage.

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run the service:
   ```bash
   poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

## Features
- Epic FHIR API integration
- Patient data storage and retrieval
- Biometric data management
- Medical history tracking 