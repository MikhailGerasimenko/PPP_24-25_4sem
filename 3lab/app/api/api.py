from fastapi import APIRouter
from app.api.endpoints import bruteforce

router = APIRouter()
router.include_router(bruteforce.router, prefix="/bruteforce", tags=["bruteforce"]) 