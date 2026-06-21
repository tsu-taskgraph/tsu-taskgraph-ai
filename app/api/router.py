from fastapi import APIRouter

from app.api import health
from app.api.v1 import router as v1_router

router = APIRouter()
router.include_router(health.router, tags=["Health"])
router.include_router(v1_router.router, prefix="/api/v1")
