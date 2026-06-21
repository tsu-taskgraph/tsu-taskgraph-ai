from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.utils import (
    build_messages,
    extract_json,
    handle_provider_error,
    map_common_params,
)
from app.schemas.common import ProviderConfig


class OpenAIProvider(BaseProvider):
    BASE_URL = "https://api.openai.com/v1"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def _build_params(self, settings: dict[str, Any] | None) -> dict[str, Any]:
        params = map_common_params(settings)
        if settings:
            reasoning_effort = settings.get("reasoningEffort")
            if reasoning_effort and self.config.model and self.config.model.startswith("o"):
                params["reasoning_effort"] = reasoning_effort
                params.pop("temperature", None)
        return params

    async def _chat_completion(
        self,
        messages: list[dict[str, str]],
        json_mode: bool = True,
    ) -> dict[str, Any]:
        model = self.config.model or "gpt-4o"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        payload.update(self._build_params(self.config.settings.model_dump(by_alias=True)
                                          if self.config.settings else None))
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            handle_provider_error(str(e), e.response.status_code)
        except httpx.RequestError as e:
            handle_provider_error(str(e))

        content = data["choices"][0]["message"]["content"]
        return extract_json(content)

    async def check(self) -> dict[str, Any]:
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            return {"available": True, "latency_ms": int(response.elapsed.total_seconds() * 1000), "error": None}
        except httpx.HTTPError as e:
            return {"available": False, "latency_ms": None, "error": str(e)}

    async def generate_skeleton(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical lead. Generate a task graph skeleton for a software project. "
            "Return a JSON object with fields: nodes (array of {tempId, title, description, category, estimatedHours}) "
            "and edges (array of {sourceTempId, targetTempId}). "
            "Categories: BACKEND, FRONTEND, DEVOPS, TESTING, DOCUMENTATION, DESIGN, OTHER."
        )
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Tech stack: {', '.join(prompt_data.get('techStack', []))}\n"
            f"Description: {prompt_data.get('description')}\n"
            f"Team size: {prompt_data.get('teamSize', 1)}\n"
            f"Include estimatedHours: {prompt_data.get('aiEstimate', True)}"
        )
        result = await self._chat_completion(build_messages(system, user))
        return {
            "nodes": result.get("nodes", []),
            "edges": result.get("edges", []),
            "totalEstimatedHours": sum(n.get("estimatedHours", 0) for n in result.get("nodes", [])
                                       if n.get("estimatedHours")),
            "modelUsed": self.config.model or "gpt-4o",
            "provider": self.config.provider,
        }

    async def enrich_task(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical mentor. Enrich a single task with actionable details. "
            "Return JSON with fields: checklist (array of strings), pitfalls (array of strings), "
            "links (array of {title, url}), rawMarkdown (string), wikiDraft (string)."
        )
        task = prompt_data.get("task", {})
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Tech stack: {', '.join(prompt_data.get('techStack', []))}\n"
            f"Task: {task.get('taskTitle')}\n"
            f"Description: {task.get('taskDescription')}\n"
            f"Category: {task.get('category')}\n"
            f"Predecessors: {', '.join(task.get('predecessorTitles', []))}\n"
            f"Successors: {', '.join(task.get('successorTitles', []))}"
        )
        result = await self._chat_completion(build_messages(system, user))
        return {
            "taskId": task.get("taskId"),
            "checklist": result.get("checklist", []),
            "pitfalls": result.get("pitfalls", []),
            "links": result.get("links", []),
            "rawMarkdown": result.get("rawMarkdown", ""),
            "wikiDraft": result.get("wikiDraft") if prompt_data.get("generateWikiDraft") else None,
            "modelUsed": self.config.model or "gpt-4o",
            "provider": self.config.provider,
        }

    async def mutate_graph(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical lead. Given a current task graph and a user request, "
            "return a JSON patch with fields: newNodes (array of {tempId, title, description, category, "
            "estimatedHours}),"
            "newEdges (array of {sourceTempIdOrUuid, targetTempIdOrUuid}), recalculatedTotalHours (optional), "
            "reasoning (optional)."
        )
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Tech stack: {', '.join(prompt_data.get('techStack', []))}\n"
            f"User request: {prompt_data.get('prompt')}\n"
            f"Current graph: {prompt_data.get('currentGraph')}"
        )
        result = await self._chat_completion(build_messages(system, user))
        return {
            "patch": {
                "newNodes": result.get("newNodes", []),
                "newEdges": result.get("newEdges", []),
                "recalculatedTotalHours": result.get("recalculatedTotalHours"),
                "reasoning": result.get("reasoning"),
            },
            "modelUsed": self.config.model or "gpt-4o",
            "provider": self.config.provider,
        }

    async def smart_recovery(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical lead. A graph mutation created a cycle. Fix the patch so the graph remains acyclic. "
            "Return JSON with fields: newNodes, newEdges, recalculatedTotalHours, reasoning."
        )
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Tech stack: {', '.join(prompt_data.get('techStack', []))}\n"
            f"Cycle nodes: {prompt_data.get('cycleNodes')}\n"
            f"Failed patch: {prompt_data.get('failedMutation')}\n"
            f"Current graph: {prompt_data.get('currentGraph')}"
        )
        result = await self._chat_completion(build_messages(system, user))
        return {
            "fixedPatch": {
                "newNodes": result.get("newNodes", []),
                "newEdges": result.get("newEdges", []),
                "recalculatedTotalHours": result.get("recalculatedTotalHours"),
                "reasoning": result.get("reasoning"),
            },
            "recoveryNote": result.get("recoveryNote", "Patch corrected to avoid cycles"),
            "modelUsed": self.config.model or "gpt-4o",
            "provider": self.config.provider,
        }

    async def generate_diagrams(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a software architect. Generate Mermaid.js diagrams from a project graph. "
            "Return JSON with fields: c4Code (string or null), sequenceCode (string or null), classCode (string or "
            "null)."
        )
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Tech stack: {', '.join(prompt_data.get('techStack', []))}\n"
            f"Nodes: {prompt_data.get('nodes')}\n"
            f"Edges: {prompt_data.get('edges')}\n"
            f"Requested diagrams: {prompt_data.get('requestedDiagrams', ['c4', 'sequence', 'class'])}"
        )
        result = await self._chat_completion(build_messages(system, user))
        return {
            "c4Code": result.get("c4Code"),
            "sequenceCode": result.get("sequenceCode"),
            "classCode": result.get("classCode"),
            "modelUsed": self.config.model or "gpt-4o",
            "provider": self.config.provider,
        }

    async def generate_wiki(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a technical writer. Generate a Wiki page for a task. "
            "Return JSON with fields: title (string), content (string in Markdown)."
        )
        task = prompt_data.get("task", {})
        user = (
            f"Project: {prompt_data.get('projectName')}\n"
            f"Tech stack: {', '.join(prompt_data.get('techStack', []))}\n"
            f"Task: {task.get('taskTitle')}\n"
            f"Description: {task.get('taskDescription')}\n"
            f"Checklist: {task.get('checklist', [])}\n"
            f"Pitfalls: {task.get('pitfalls', [])}\n"
            f"Existing content: {prompt_data.get('existingContent') or 'None'}"
        )
        result = await self._chat_completion(build_messages(system, user))
        return {
            "title": result.get("title", task.get("taskTitle", "Wiki page")),
            "content": result.get("content", ""),
            "modelUsed": self.config.model or "gpt-4o",
            "provider": self.config.provider,
        }
