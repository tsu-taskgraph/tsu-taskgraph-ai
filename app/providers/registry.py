from typing import Any

from fastapi import HTTPException, status

from app.providers.base import BaseProvider
from app.providers.openai import OpenAIProvider
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.groq import GroqProvider
from app.providers.mistral import MistralProvider
from app.schemas.common import ProviderConfig


class StubProvider(BaseProvider):

    @property
    def default_model(self) -> str:
        return "stub"

    @property
    def check_url(self) -> str:
        return "/stub-health"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = None  # type: ignore[assignment]

    async def _call_llm(
        self,
        system: str,
        user: str,
        json_mode: bool = True,
    ) -> dict[str, Any]:
        raise NotImplementedError("StubProvider does not call LLM")

    async def check(self) -> dict[str, Any]:
        return {"available": True, "latency_ms": 1, "error": None}

    async def generate_skeleton(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "tempId": "node_1",
                    "title": "Инициализация проекта",
                    "description": "Создание репозитория и базовой структуры",
                    "category": "DEVOPS",
                    "estimatedHours": 2.0,
                },
                {
                    "tempId": "node_2",
                    "title": "Настройка зависимостей",
                    "description": "Установка ключевых библиотек",
                    "category": "BACKEND",
                    "estimatedHours": 3.0,
                },
            ],
            "edges": [
                {"sourceTempId": "node_1", "targetTempId": "node_2"},
            ],
            "totalEstimatedHours": 5.0,
            "modelUsed": "stub",
            "provider": self.config.provider,
        }

    async def enrich_task(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "taskId": prompt_data.get("task", {}).get("taskId"),
            "checklist": ["Шаг 1", "Шаг 2"],
            "pitfalls": ["Подводный камень 1"],
            "links": [],
            "rawMarkdown": "# Markdown черновик",
            "wikiDraft": "# Wiki драфт",
            "modelUsed": "stub",
            "provider": self.config.provider,
        }

    async def mutate_graph(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "patch": {
                "newNodes": [],
                "newEdges": [],
                "recalculatedTotalHours": None,
                "reasoning": "Stub reasoning",
            },
            "modelUsed": "stub",
            "provider": self.config.provider,
        }

    async def smart_recovery(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "fixedPatch": {
                "newNodes": [],
                "newEdges": [],
                "recalculatedTotalHours": None,
                "reasoning": "Stub recovery",
            },
            "recoveryNote": "Stub recovery note",
            "modelUsed": "stub",
            "provider": self.config.provider,
        }

    async def generate_diagrams(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        requested = prompt_data.get("requestedDiagrams", ["c4", "sequence", "class"])
        project_name = prompt_data.get("projectName", "Project")

        c4 = None
        if "c4" in requested:
            c4 = (
                f"C4Context\n"
                f"  title System Context - {project_name}\n"
                f"  Person(user, \"User\", \"End user\")\n"
                f"  System(frontend, \"Frontend SPA\", \"React\")\n"
                f"  System(backend, \"Core API\", \"Spring Boot\")\n"
                f"  SystemDb(db, \"Database\", \"PostgreSQL\")\n"
                f"  Rel(user, frontend, \"Uses\")\n"
                f"  Rel(frontend, backend, \"REST API\")\n"
                f"  Rel(backend, db, \"Reads/Writes\")"
            )

        seq = None
        if "sequence" in requested:
            seq = (
                "sequenceDiagram\n"
                "  participant Client\n"
                "  participant API\n"
                "  participant DB\n"
                "  Client->>API: POST /api/resource\n"
                "  API->>DB: INSERT INTO resources\n"
                "  DB-->>API: OK\n"
                "  API-->>Client: 201 Created"
            )

        cls = None
        if "class" in requested:
            cls = (
                "classDiagram\n"
                "  class ProjectSetup {\n"
                "    <<DEVOPS>>\n"
                "    +initRepository()\n"
                "    +configureCi()\n"
                "  }\n"
                "  class CoreAPI {\n"
                "    <<BACKEND>>\n"
                "    +defineEndpoints()\n"
                "    +addValidation()\n"
                "  }\n"
                "  ProjectSetup <|-- CoreAPI"
            )

        return {
            "c4Code": c4,
            "sequenceCode": seq,
            "classCode": cls,
            "modelUsed": "stub",
            "provider": self.config.provider,
        }

    async def generate_wiki(self, prompt_data: dict[str, Any]) -> dict[str, Any]:
        task = prompt_data.get("task", {})
        task_title = task.get("taskTitle", "Wiki page")
        existing = prompt_data.get("existingContent")

        if existing:
            content = (
                f"# {task_title}\n\n"
                f"## Overview\n\n"
                f"This is a regenerated version of the Wiki page.\n\n"
                f"## Previous Content (preserved)\n\n"
                f"{existing}\n\n"
                f"## Enhanced Details\n\n"
                f"Additional technical details added by AI during regeneration.\n"
            )
        else:
            content = (
                f"# {task_title}\n\n"
                f"## Overview\n\n"
                f"This task is part of the project plan. "
                f"It covers the implementation details and requirements.\n\n"
                f"## Implementation Guide\n\n"
                f"1. Set up the development environment\n"
                f"2. Implement core functionality\n"
                f"3. Write tests\n"
                f"4. Document the implementation\n\n"
                f"## Potential Pitfalls\n\n"
                f"- Ensure proper error handling\n"
                f"- Consider edge cases\n\n"
                f"## Resources\n\n"
                f"- Official documentation\n"
            )

        return {
            "title": task_title,
            "content": content,
            "modelUsed": "stub",
            "provider": self.config.provider,
        }


def get_provider(config: ProviderConfig) -> BaseProvider:
    if config.provider != "ollama" and not config.api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key is required for provider '{config.provider}'",
        )

    providers = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "groq": GroqProvider,
        "mistral": MistralProvider,
        "ollama": OllamaProvider,
    }

    provider_class = providers.get(config.provider)
    if not provider_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider '{config.provider}'",
        )

    return provider_class(config)


PROVIDERS_DIRECTORY = {
    "gemini": {
        "defaultModel": "gemini-3.5-flash",
        "supportedModels": [
            "gemini-3.5-flash",
            "gemini-3.1-pro",
            "gemini-3-pro",
            "gemini-3-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash"
        ]
    },
    "openai": {
        "defaultModel": "gpt-5.3-instant",
        "supportedModels": [
            "gpt-5.4",
            "gpt-5.3-instant",
            "gpt-5-mini",
            "gpt-5-nano",
            "o4-mini",
            "o3-mini",
            "gpt-4o",
            "gpt-4o-mini"
        ]
    },
    "anthropic": {
        "defaultModel": "claude-sonnet-4.6",
        "supportedModels": [
            "claude-fable-5",
            "claude-opus-4.8",
            "claude-sonnet-4.6",
            "claude-haiku-4.5",
            "claude-3-7-sonnet",
            "claude-3-5-sonnet"
        ]
    },
    "groq": {
        "defaultModel": "llama-3.3-70b-versatile",
        "supportedModels": [
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-3.1-8b-instant",
            "groq/compound",
            "groq/compound-mini"
        ]
    },
    "mistral": {
        "defaultModel": "mistral-large-latest",
        "supportedModels": [
            "mistral-large-latest",
            "codestral-latest",
            "mistral-medium-latest",
            "mistral-small-latest"
        ]
    },
    "ollama": {
        "defaultModel": "llama3",
        "supportedModels": [
            "llama3",
            "mistral",
            "qwen2.5-coder",
            "phi3",
            "gemma2"
        ]
    }
}
