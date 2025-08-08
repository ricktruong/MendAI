import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.core.logger import configure_logging
from .api.v0.routes import api_router

# Configure logging
configure_logging()
log = structlog.get_logger()

# Create FastAPI app
app = FastAPI()

# Allow all origins for now (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Backend Engine is running!"}

