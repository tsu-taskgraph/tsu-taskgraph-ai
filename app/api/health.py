from fastapi import APIRouter, Depends

from app.config import get_settings
from app.core.security import require_internal_secret
from app.providers.registry import get_provider
from app.schemas.health import HealthResponse, ProviderCheckResponse
from app.schemas.common import ProviderConfig

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="healthy", version=settings.app_version)


@router.post(
    "/health/providers",
    response_model=ProviderCheckResponse,
    dependencies=[Depends(require_internal_secret)],
)
async def check_provider(payload: dict) -> ProviderCheckResponse:
    config = ProviderConfig(**payload.get("providerConfig", {}))
    provider = get_provider(config)
    result = await provider.check()
    return ProviderCheckResponse(provider=config.provider, **result)
