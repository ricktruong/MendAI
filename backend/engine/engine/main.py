import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.core.logger import configure_logging
from .routes.chat import router as chat_router
from .routes.ai_analysis import router as ai_analysis_router
from .routes.dashboard import router as dashboard_router
from .routes.login import router as login_router

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
app.include_router(chat_router)
app.include_router(ai_analysis_router)
app.include_router(dashboard_router)
app.include_router(login_router)

@app.get("/")
def read_root():
    return {"message": "Backend Engine is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "backend-engine"}

