from fastapi import APIRouter

from .endpoints import *

api_router = APIRouter(prefix="/v0")
# include all the endpoints