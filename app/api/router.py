from fastapi import APIRouter

from app.api import health
from app.api.v1 import ai

router = APIRouter()
router.include_router(health.router, tags=["Health"])
router.include_router(ai.router, prefix="/api/v1")
