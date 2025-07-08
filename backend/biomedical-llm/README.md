# Biomedical LLM Service

This service provides AI-assisted patient prognosis using MONAI multimodal models and LLMs for biomedical chatbot functionality.

## Setup

REQUIRES GPU SUPPORT

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run the service:
   ```bash
   poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8003
   ```

## Features
- Multimodal image-text processing
- Biomedical chatbot
- Patient prognosis assistance
- MONAI + Transformers integration 