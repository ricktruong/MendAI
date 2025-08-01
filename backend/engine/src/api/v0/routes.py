from fastapi import APIRouter

from .endpoints import login_page

api_router = APIRouter(prefix="/v0")
api_router.include_router(login_page.router)
