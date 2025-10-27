from dotenv import load_dotenv
from pathlib import Path

# Load .env file from current directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from patient_data.routes import patients, observations, encounters, conditions, medications, chat

app = FastAPI(
    title="MendAI Patient Data API",
    version="1.0.0",
    description="FHIR-integrated backend API for patient data access from Google Healthcare API."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router, prefix="/api")
app.include_router(observations.router, prefix="/api")
app.include_router(encounters.router, prefix="/api")
app.include_router(conditions.router, prefix="/api")
app.include_router(medications.router, prefix="/api")
app.include_router(chat.router, prefix="/api/clinical")  # Changed from /api to /api/clinical

@app.get("/")
def read_root():
    return {
        "message": "Patient Data Service is running!",
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}