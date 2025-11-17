from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from medical_imaging.routes.analysis import router

app = FastAPI()

# Allow all origins for now (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Imaging Service is running!"} 