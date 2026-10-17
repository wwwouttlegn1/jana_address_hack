from fastapi import APIRouter

from app.api.routes import challenge, health


api_router = APIRouter()
api_router.include_router(challenge.router, tags=["JANA ADDRESS"])
api_router.include_router(health.router, prefix="/health", tags=["Система"])
