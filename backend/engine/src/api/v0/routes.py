from fastapi import APIRouter

from .endpoints import *

api_router = APIRouter(prefix="/v0")

# TODO: include all the endpoints
# Frontend -> Backend Engine endpoints
# 1. Login Page
# I. Doctor Account Login Request

# 2. Dashboard Page
# I. Select Patient Request
# II. Logout Request?

# 3. Chat Page
# I.User Message Request


# Frontend <- Backend Engine endpoints

# Backend Engine -> Patient Data Service endpoints

# Backend Engine <- Patient Data Service endpoints

# Backend Engine -> LLM Service endpoints

# Backend Engine <- LLM Service endpoints

