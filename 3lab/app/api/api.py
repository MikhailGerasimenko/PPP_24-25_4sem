from fastapi import APIRouter

from .endpoints import bruteforce_router

api_router = APIRouter()
api_router.include_router(bruteforce_router, prefix="/bruteforce", tags=["bruteforce"]) 