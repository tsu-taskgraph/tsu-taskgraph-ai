import asyncio
import httpx
from celery import Celery

from app.config import get_settings
from app.providers.registry import get_provider
from app.schemas.common import ProviderConfig

settings = get_settings()

celery_app = Celery(
    "taskgraph_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=3)
def enrich_task_background(self, task_request_data: dict, job_id: str) -> None:

    async def run_enrichment():
        provider_config_dict = task_request_data.get("providerConfig", {})
        provider_config = ProviderConfig(**provider_config_dict)
        provider = get_provider(provider_config)

        try:
            result = await provider.enrich_task(task_request_data)

            callback_payload = {
                "jobId": job_id,
                "taskId": task_request_data.get("task", {}).get("taskId"),
                "status": "SUCCESS",
                "result": result,
                "checklist": result.get("checklist", []),
                "pitfalls": result.get("pitfalls", []),
                "links": result.get("links", []),
                "rawMarkdown": result.get("rawMarkdown", ""),
                "wikiDraft": result.get("wikiDraft"),
                "error": None,
                "providerError": None
            }
        except Exception as e:
            callback_payload = {
                "jobId": job_id,
                "taskId": task_request_data.get("task", {}).get("taskId"),
                "status": "FAILED",
                "result": None,
                "checklist": None,
                "pitfalls": None,
                "links": None,
                "rawMarkdown": None,
                "wikiDraft": None,
                "error": str(e),
                "providerError": str(e)
            }
        finally:
            if hasattr(provider, "client") and provider.client is not None:
                await provider.client.aclose()

        callback_url = task_request_data.get("callbackUrl")
        headers = {
            "X-Internal-Secret": settings.internal_secret,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(callback_url, json=callback_payload, headers=headers)
                response.raise_for_status()
            except Exception as cb_err:
                print(f"Callback delivery failed to {callback_url}: {cb_err}")

    asyncio.run(run_enrichment())
