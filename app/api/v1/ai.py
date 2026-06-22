from fastapi import APIRouter, Depends, status

from app.core.security import require_internal_secret
from app.core.exceptions import ErrorResponse
from app.providers.registry import get_provider
from app.schemas.diagrams import DiagramRequest, DiagramResponse
from app.schemas.enrichment import EnrichTaskRequest, EnrichTaskJobResponse
from app.schemas.mutation import MutateGraphRequest, MutateGraphResponse
from app.schemas.recovery import SmartRecoveryRequest, SmartRecoveryResponse
from app.schemas.skeleton import GenerateSkeletonRequest, GenerateSkeletonResponse
from app.schemas.wiki import GenerateWikiRequest, GenerateWikiResponse
from app.schemas.health import ProviderCheckRequest

router = APIRouter(dependencies=[Depends(require_internal_secret)])

COMMON_AI_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request - Неверные входные данные"},
    401: {"model": ErrorResponse, "description": "Unauthorized - Отсутствует или невалидный X-Internal-Secret или "
                                                 "API-ключ ИИ"},
    422: {"model": ErrorResponse, "description": "Unprocessable Entity - Ошибка валидации структуры или невалидный "
                                                 "ответ ИИ"},
    429: {"model": ErrorResponse, "description": "Too Many Requests - Превышен лимит запросов (Rate limit) у провайдера"},
    502: {"model": ErrorResponse, "description": "Bad Gateway - Сбой ИИ-провайдера"},
    504: {"model": ErrorResponse, "description": "Gateway Timeout - Превышено время ожидания ответа ИИ"},
}


@router.post(
    "/skeleton",
    response_model=GenerateSkeletonResponse,
    responses=COMMON_AI_RESPONSES,
    tags=["Graph Generation"]
)
async def generate_skeleton(body: GenerateSkeletonRequest) -> GenerateSkeletonResponse:
    provider = get_provider(body.provider_config)
    result = await provider.generate_skeleton(body.model_dump(by_alias=True))
    return GenerateSkeletonResponse(**result)


@router.post(
    "/enrich-task",
    response_model=EnrichTaskJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Ошибка во входных данных"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Невалидный X-Internal-Secret"},
        422: {"model": ErrorResponse, "description": "Unprocessable Entity - Ошибка валидации структуры запроса"},
        503: {"model": ErrorResponse, "description": "Service Unavailable - Очередь Celery недоступна"},
    },
    tags=["Task Enrichment"]
)
async def enrich_task(body: EnrichTaskRequest) -> EnrichTaskJobResponse:
    import uuid
    from app.core.celery_app import enrich_task_background

    job_id = str(uuid.uuid4())

    enrich_task_background.delay(
        body.model_dump(by_alias=True),
        job_id
    )

    return EnrichTaskJobResponse(
        job_id=job_id,
        task_id=body.task.task_id,
        status="QUEUED",
        estimated_seconds=8,
    )


@router.post(
    "/mutate",
    response_model=MutateGraphResponse,
    responses=COMMON_AI_RESPONSES,
    tags=["Graph Mutation"]
)
async def mutate_graph(body: MutateGraphRequest) -> MutateGraphResponse:
    provider = get_provider(body.provider_config)
    result = await provider.mutate_graph(body.model_dump(by_alias=True))
    return MutateGraphResponse(**result)


@router.post(
    "/smart-recovery",
    response_model=SmartRecoveryResponse,
    responses=COMMON_AI_RESPONSES,
    tags=["Smart Recovery"]
)
async def smart_recovery(body: SmartRecoveryRequest) -> SmartRecoveryResponse:
    provider = get_provider(body.provider_config)
    result = await provider.smart_recovery(body.model_dump(by_alias=True))
    return SmartRecoveryResponse(**result)


@router.post(
    "/diagrams",
    response_model=DiagramResponse,
    responses=COMMON_AI_RESPONSES,
    tags=["Diagrams"]
)
async def generate_diagrams(body: DiagramRequest) -> DiagramResponse:
    provider = get_provider(body.provider_config)
    result = await provider.generate_diagrams(body.model_dump(by_alias=True))
    return DiagramResponse(**result)


@router.post(
    "/wiki",
    response_model=GenerateWikiResponse,
    responses=COMMON_AI_RESPONSES,
    tags=["Wiki"]
)
async def generate_wiki(body: GenerateWikiRequest) -> GenerateWikiResponse:
    provider = get_provider(body.provider_config)
    result = await provider.generate_wiki(body.model_dump(by_alias=True))
    return GenerateWikiResponse(**result)


@router.get(
    "/providers",
    response_model=list[str],
    tags=["Providers"]
)
async def list_providers() -> list[str]:
    from app.providers.registry import PROVIDERS_DIRECTORY
    return list(PROVIDERS_DIRECTORY.keys())


@router.post(
    "/providers/models",
    response_model=list[str],
    responses=COMMON_AI_RESPONSES,
    tags=["Providers"]
)
async def list_realtime_models(body: ProviderCheckRequest) -> list[str]:
    provider = get_provider(body.provider_config)
    try:
        models = await provider.list_models()
    finally:
        if hasattr(provider, "client") and provider.client is not None:
            await provider.client.aclose()
    return models
