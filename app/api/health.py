from fastapi import APIRouter, Depends

from app.config import get_settings
from app.core.security import require_internal_secret
from app.core.exceptions import ErrorResponse
from app.providers.registry import get_provider
from app.schemas.health import HealthResponse, ProviderCheckResponse, ProviderCheckRequest

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="healthy", version=settings.app_version)


@router.post(
    "/health/providers",
    response_model=ProviderCheckResponse,
    dependencies=[Depends(require_internal_secret)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Невалидный X-Internal-Secret"},
    }
)
async def check_provider(body: ProviderCheckRequest) -> ProviderCheckResponse:
    provider = get_provider(body.provider_config)

    try:
        result = await provider.check()
    finally:
        if hasattr(provider, "client") and provider.client is not None:
            await provider.client.aclose()

    return ProviderCheckResponse(provider=body.provider_config.provider, **result)
