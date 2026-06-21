import httpx
from typing import Any

from app.providers.base import BaseProvider
from app.providers.utils import build_messages, extract_json, handle_provider_error
from app.schemas.common import ProviderConfig


def _build_options(settings: dict[str, Any] | None) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if not settings:
        return options
    if settings.get("temperature") is not None:
        options["temperature"] = settings["temperature"]
    if settings.get("ollamaNumCtx") is not None:
        options["num_ctx"] = settings["ollamaNumCtx"]
    if settings.get("ollamaNumGpu") is not None:
        options["num_gpu"] = settings["ollamaNumGpu"]
    return options


class OllamaProvider(BaseProvider):
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        base_url = config.ollama_base_url or self.DEFAULT_BASE_URL
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=120.0,
        )

    async def _chat(self, system: str, user: str, json_mode: bool = True) -> dict[str, Any]:
        model = self.config.model or "llama3"
        settings_dict = self.config.settings.model_dump(by_alias=True) if self.config.settings else None
        payload: dict[str, Any] = {
            "model": model,
            "messages": build_messages(system, user),
            "stream": False,
            "options": _build_options(settings_dict),
        }
        if json_mode:
            payload["format"] = "json"

        try:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            handle_provider_error(str(e), e.response.status_code)
            return {}
        except httpx.RequestError as e:
            handle_provider_error(str(e))
            return {}

        text = data["message"]["content"]
        return extract_json(text)

    async def check(self) -> dict[str, Any]:
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            models = [m["name"] for m in response.json().get("models", [])]
            return {"available": True, "latency_ms": int(response.elapsed.total_seconds() * 1000),
                    "error": None, "ollamaModels": models}
        except httpx.HTTPError as e:
            return {"available": False, "latency_ms": None, "error": str(e), "ollamaModels": None}

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
        result = await self._chat(system, user)
        return {
            "nodes": result.get("nodes", []),
            "edges": result.get("edges", []),
            "totalEstimatedHours": sum(n.get("estimatedHours", 0) for n in result.get("nodes", [])
                                       if n.get("estimatedHours")),
            "modelUsed": self.config.model or "llama3",
            "provider": self.config.provider,
        }

    async def enrich_task(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = ("You are a technical mentor. Enrich a task. Return JSON with checklist, pitfalls, links, "
                  "rawMarkdown, wikiDraft.")
        task = prompt_data.get("task", {})
        user = f"Task: {task.get('taskTitle')}\nDescription: {task.get('taskDescription')}"
        result = await self._chat(system, user)
        return {
            "taskId": task.get("taskId"),
            "checklist": result.get("checklist", []),
            "pitfalls": result.get("pitfalls", []),
            "links": result.get("links", []),
            "rawMarkdown": result.get("rawMarkdown", ""),
            "wikiDraft": result.get("wikiDraft") if prompt_data.get("generateWikiDraft") else None,
            "modelUsed": self.config.model or "llama3",
            "provider": self.config.provider,
        }

    async def mutate_graph(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = ("You are a technical lead. Return a JSON patch with newNodes, newEdges, recalculatedTotalHours, "
                  "reasoning.")
        user = f"Request: {prompt_data.get('prompt')}\nCurrent graph: {prompt_data.get('currentGraph')}"
        result = await self._chat(system, user)
        return {
            "patch": {
                "newNodes": result.get("newNodes", []),
                "newEdges": result.get("newEdges", []),
                "recalculatedTotalHours": result.get("recalculatedTotalHours"),
                "reasoning": result.get("reasoning"),
            },
            "modelUsed": self.config.model or "llama3",
            "provider": self.config.provider,
        }

    async def smart_recovery(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = ("You are a technical lead. Fix a cyclic patch. Return JSON with newNodes, newEdges, "
                  "recalculatedTotalHours, reasoning.")
        user = f"Cycle nodes: {prompt_data.get('cycleNodes')}\nFailed patch: {prompt_data.get('failedMutation')}"
        result = await self._chat(system, user)
        return {
            "fixedPatch": {
                "newNodes": result.get("newNodes", []),
                "newEdges": result.get("newEdges", []),
                "recalculatedTotalHours": result.get("recalculatedTotalHours"),
                "reasoning": result.get("reasoning"),
            },
            "recoveryNote": result.get("recoveryNote", "Patch corrected to avoid cycles"),
            "modelUsed": self.config.model or "llama3",
            "provider": self.config.provider,
        }

    async def generate_diagrams(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = ("You are a software architect. Generate Mermaid diagrams. Return JSON with c4Code, sequenceCode, "
                  "classCode.")
        user = (f"Project: {prompt_data.get('projectName')}\nNodes: {prompt_data.get('nodes')}\nEdges: "
                f"{prompt_data.get('edges')}")
        result = await self._chat(system, user)
        return {
            "c4Code": result.get("c4Code"),
            "sequenceCode": result.get("sequenceCode"),
            "classCode": result.get("classCode"),
            "modelUsed": self.config.model or "llama3",
            "provider": self.config.provider,
        }

    async def generate_wiki(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = "You are a technical writer. Generate a Wiki page in Markdown. Return JSON with title and content."
        task = prompt_data.get("task", {})
        user = f"Task: {task.get('taskTitle')}\nDescription: {task.get('taskDescription')}"
        result = await self._chat(system, user)
        return {
            "title": result.get("title", task.get("taskTitle", "Wiki page")),
            "content": result.get("content", ""),
            "modelUsed": self.config.model or "llama3",
            "provider": self.config.provider,
        }
