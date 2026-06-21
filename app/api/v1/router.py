from fastapi import APIRouter

from app.api.v1 import ai

router = APIRouter()
router.include_router(ai.router, prefix="/ai")
