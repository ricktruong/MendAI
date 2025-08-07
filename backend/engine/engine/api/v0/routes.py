from fastapi import APIRouter

from .endpoints import login, dashboard, chat

api_router = APIRouter(prefix="/v0")
api_router.include_router(login.router)
api_router.include_router(dashboard.router)
api_router.include_router(chat.router)
