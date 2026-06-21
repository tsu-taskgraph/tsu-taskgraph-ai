from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.schemas.common import ProviderConfig


class BaseProvider(ABC):

    def __init__(self, config: ProviderConfig):
        self.config = config

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

    async def check(self) -> dict[str, Any]:
        try:
            response = await self.client.get(self.check_url)  # type: ignore[attr-defined]
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
        system = (
            "You are a technical lead. Generate a task graph skeleton for a software project. "
            "Return a JSON object with fields: nodes and edges."
        )
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Tech stack: {', '.join(prompt_data.get('techStack', []))}\n"
            f"Description: {prompt_data.get('description')}"
        )
        result = await self._call_llm(system, user)
        return {
            "nodes": result.get("nodes", []),
            "edges": result.get("edges", []),
            "totalEstimatedHours": sum(
                n.get("estimatedHours", 0)
                for n in result.get("nodes", [])
                if n.get("estimatedHours")
            ),
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def enrich_task(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical mentor. Enrich a task. Return JSON with checklist, pitfalls, links, "
            "rawMarkdown, wikiDraft."
        )
        task = prompt_data.get("task", {})
        user = f"Task: {task.get('taskTitle')}\nDescription: {task.get('taskDescription')}"
        result = await self._call_llm(system, user)
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
        system = (
            "You are a technical lead. Return a JSON patch with newNodes, newEdges, "
            "recalculatedTotalHours, reasoning."
        )
        user = f"Request: {prompt_data.get('prompt')}\nCurrent graph: {prompt_data.get('currentGraph')}"
        result = await self._call_llm(system, user)
        return {
            "patch": {
                "newNodes": result.get("newNodes", []),
                "newEdges": result.get("newEdges", []),
                "recalculatedTotalHours": result.get("recalculatedTotalHours"),
                "reasoning": result.get("reasoning"),
            },
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def smart_recovery(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical lead. Fix a cyclic patch. Return JSON with newNodes, newEdges, "
            "recalculatedTotalHours, reasoning."
        )
        user = (
            f"Cycle nodes: {prompt_data.get('cycleNodes')}\n"
            f"Failed patch: {prompt_data.get('failedMutation')}"
        )
        result = await self._call_llm(system, user)
        return {
            "fixedPatch": {
                "newNodes": result.get("newNodes", []),
                "newEdges": result.get("newEdges", []),
                "recalculatedTotalHours": result.get("recalculatedTotalHours"),
                "reasoning": result.get("reasoning"),
            },
            "recoveryNote": result.get("recoveryNote", "Patch corrected to avoid cycles"),
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def generate_diagrams(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a software architect. Generate Mermaid diagrams. Return JSON with "
            "c4Code, sequenceCode, classCode."
        )
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Nodes: {prompt_data.get('nodes')}\n"
            f"Edges: {prompt_data.get('edges')}"
        )
        result = await self._call_llm(system, user)
        return {
            "c4Code": result.get("c4Code"),
            "sequenceCode": result.get("sequenceCode"),
            "classCode": result.get("classCode"),
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }

    async def generate_wiki(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical writer. Generate a Wiki page in Markdown. "
            "Return JSON with title and content."
        )
        task = prompt_data.get("task", {})
        user = f"Task: {task.get('taskTitle')}\nDescription: {task.get('taskDescription')}"
        result = await self._call_llm(system, user)
        return {
            "title": result.get("title", task.get("taskTitle", "Wiki page")),
            "content": result.get("content", ""),
            "modelUsed": self.config.model or self.default_model,
            "provider": self.config.provider,
        }
