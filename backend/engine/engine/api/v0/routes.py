from fastapi import APIRouter

from .endpoints import login, dashboard, chat, ai_analysis

api_router = APIRouter(prefix="/v0")
api_router.include_router(login.router)
api_router.include_router(dashboard.router)
api_router.include_router(chat.router)
api_router.include_router(ai_analysis.router)
