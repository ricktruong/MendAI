"""
Biomedical LLM Service
Main FastAPI application for AI-powered clinical consultation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import os
from dotenv import load_dotenv

from .routes.chat import router as chat_router
from .config import get_settings
from common.core.logger import configure_logging

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Configure logging
configure_logging()
logger = structlog.get_logger()

# Get settings
settings = get_settings()
logger.info(f"Starting {settings.service_name} on port {settings.service_port}")

# Create FastAPI app
app = FastAPI(
    title="Biomedical LLM Service",
    description="AI-powered clinical consultation using OpenAI with biomedical context",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, tags=["chat"])


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Biomedical LLM Service is running!",
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "openai_configured": bool(settings.openai_api_key),
        "patient_data_url": settings.patient_data_url
    } 