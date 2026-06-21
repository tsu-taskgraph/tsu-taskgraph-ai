from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.providers.prompts import build_prompt
from app.schemas.common import ProviderConfig


class BaseProvider(ABC):

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client: httpx.AsyncClient | None = None

    @property
    @abstractmethod
    def default_model(self) -> str:
        ...

    @property
    def check_url(self) -> str:
        return "/models"

    def _extra_check_fields(self, _response: httpx.Response | None) -> dict[str, Any]:
        return {}

    @abstractmethod
    async def _call_llm(
            self,
            system: str,
            user: str,
            json_mode: bool = True,
    ) -> dict[str, Any]:
        ...

    async def _call_llm_safe(
            self,
            system: str,
            user: str,
            json_mode: bool = True,
    ) -> dict[str, Any]:
        try:
            return await self._call_llm(system, user, json_mode)
        except ValueError as e:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "LlmInvalidJsonResponse",
                    "message": f"AI provider returned invalid JSON: {e}",
                    "provider": self.config.provider
                }
            )

    async def check(self) -> dict[str, Any]:
        if self.client is None:
            return {
                "available": True,
                "latency_ms": 1,
                "error": None,
            }
        try:
            response = await self.client.get(self.check_url)
            response.raise_for_status()
            return {
                "available": True,
                "latency_ms": int(response.elapsed.total_seconds() * 1000),
                "error": None,
                **self._extra_check_fields(response),
            }
        except httpx.HTTPError as e:
            return {
                "available": False,
                "latency_ms": None,
                "error": str(e),
                **self._extra_check_fields(None),
            }

    async def generate_skeleton(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system, user = build_prompt("skeleton", prompt_data)
        result = await self._call_llm_safe(system, user)

        from app.providers.utils import validate_and_clean_skeleton
        cleaned = validate_and_clean_skeleton(
            result,
            ai_estimate=prompt_data.get("aiEstimate", True)
        )

        total_estimated_hours = None
        if prompt_data.get("aiEstimate", True):
            total_estimated_hours = sum(
                n.get("estimatedHours", 0.0)
                for n in cleaned.get("nodes", [])
                if n.get("estimatedHours") is not None
            )

        return {
            "nodes": cleaned.get("nodes", []),
            "edges": cleaned.get("edges", []),
            "totalEstimatedHours": total_estimated_hours,
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def enrich_task(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system, user = build_prompt("enrich_task", prompt_data)
        task = prompt_data.get("task", {})
        result = await self._call_llm_safe(system, user)
        return {
            "taskId": task.get("taskId"),
            "checklist": result.get("checklist", []),
            "pitfalls": result.get("pitfalls", []),
            "links": result.get("links", []),
            "rawMarkdown": result.get("rawMarkdown", ""),
            "wikiDraft": result.get("wikiDraft") if prompt_data.get("generateWikiDraft") else None,
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def mutate_graph(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system, user = build_prompt("mutate_graph", prompt_data)
        result = await self._call_llm_safe(system, user)

        from app.providers.utils import validate_and_clean_mutation
        cleaned = validate_and_clean_mutation(
            result,
            current_graph=prompt_data.get("currentGraph", {}),
            ai_estimate=prompt_data.get("aiEstimate", True)
        )

        return {
            "patch": {
                "newNodes": cleaned.get("newNodes", []),
                "newEdges": cleaned.get("newEdges", []),
                "recalculatedTotalHours": cleaned.get("recalculatedTotalHours"),
                "reasoning": cleaned.get("reasoning"),
            },
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def smart_recovery(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system, user = build_prompt("smart_recovery", prompt_data)
        result = await self._call_llm_safe(system, user)

        from app.providers.utils import validate_and_clean_mutation

        patch_source = result.get("fixedPatch") or result

        cleaned = validate_and_clean_mutation(
            patch_source,
            current_graph=prompt_data.get("currentGraph", {}),
            ai_estimate=prompt_data.get("aiEstimate", True)
        )

        recovery_note = result.get("recoveryNote") or result.get(
            "recovery_note") or "The plan has been adjusted by AI to avoid loops."

        return {
            "fixedPatch": {
                "newNodes": cleaned.get("newNodes", []),
                "newEdges": cleaned.get("newEdges", []),
                "recalculatedTotalHours": cleaned.get("recalculatedTotalHours"),
                "reasoning": cleaned.get("reasoning"),
            },
            "recoveryNote": recovery_note,
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def generate_diagrams(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system, user = build_prompt("diagrams", prompt_data)
        result = await self._call_llm_safe(system, user)
        return {
            "c4Code": result.get("c4Code"),
            "sequenceCode": result.get("sequenceCode"),
            "classCode": result.get("classCode"),
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def generate_wiki(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system, user = build_prompt("wiki", prompt_data)
        task = prompt_data.get("task", {})
        result = await self._call_llm_safe(system, user)
        return {
            "title": result.get("title", task.get("taskTitle", "Wiki page")),
            "content": result.get("content", ""),
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }
