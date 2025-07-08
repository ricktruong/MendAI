from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from common.src.core.logger import configure_logging

configure_logging()

app = FastAPI()

# Allow all origins for now (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend Engine is running!"}

# You can add more routes here for proxying to microservices 