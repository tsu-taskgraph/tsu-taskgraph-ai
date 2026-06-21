from fastapi import APIRouter, Depends, status

from app.core.security import require_internal_secret
from app.providers.registry import get_provider
from app.schemas.diagrams import DiagramRequest, DiagramResponse
from app.schemas.enrichment import EnrichTaskJobResponse, EnrichTaskRequest
from app.schemas.mutation import MutateGraphRequest, MutateGraphResponse
from app.schemas.recovery import SmartRecoveryRequest, SmartRecoveryResponse
from app.schemas.skeleton import GenerateSkeletonRequest, GenerateSkeletonResponse
from app.schemas.wiki import GenerateWikiRequest, GenerateWikiResponse

router = APIRouter(dependencies=[Depends(require_internal_secret)])


@router.post("/skeleton", response_model=GenerateSkeletonResponse)
async def generate_skeleton(body: GenerateSkeletonRequest) -> GenerateSkeletonResponse:
    provider = get_provider(body.provider_config)
    result = await provider.generate_skeleton(body.model_dump(by_alias=True))
    return GenerateSkeletonResponse(**result)


@router.post(
    "/enrich-task",
    response_model=EnrichTaskJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enrich_task(body: EnrichTaskRequest) -> EnrichTaskJobResponse:
    # TODO: интегрировать Celery/RQ для фоновой обработки.
    import uuid

    return EnrichTaskJobResponse(
        job_id=str(uuid.uuid4()),
        task_id=body.task.task_id,
        status="QUEUED",
        estimated_seconds=8,
    )


@router.post("/mutate", response_model=MutateGraphResponse)
async def mutate_graph(body: MutateGraphRequest) -> MutateGraphResponse:
    provider = get_provider(body.provider_config)
    result = await provider.mutate_graph(body.model_dump(by_alias=True))
    return MutateGraphResponse(**result)


@router.post("/smart-recovery", response_model=SmartRecoveryResponse)
async def smart_recovery(body: SmartRecoveryRequest) -> SmartRecoveryResponse:
    provider = get_provider(body.provider_config)
    result = await provider.smart_recovery(body.model_dump(by_alias=True))
    return SmartRecoveryResponse(**result)


@router.post("/diagrams", response_model=DiagramResponse)
async def generate_diagrams(body: DiagramRequest) -> DiagramResponse:
    provider = get_provider(body.provider_config)
    result = await provider.generate_diagrams(body.model_dump(by_alias=True))
    return DiagramResponse(**result)


@router.post("/wiki", response_model=GenerateWikiResponse)
async def generate_wiki(body: GenerateWikiRequest) -> GenerateWikiResponse:
    provider = get_provider(body.provider_config)
    result = await provider.generate_wiki(body.model_dump(by_alias=True))
    return GenerateWikiResponse(**result)
