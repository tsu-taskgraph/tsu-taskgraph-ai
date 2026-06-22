import httpx
from typing import Any

from app.providers.base import BaseProvider
from app.providers.utils import build_messages, extract_json, safe_post
from app.schemas.common import ProviderConfig


class OllamaProvider(BaseProvider):
    DEFAULT_BASE_URL = "http://localhost:11434"

    @property
    def default_model(self) -> str:
        return "llama3"

    @property
    def check_url(self) -> str:
        return "/api/tags"

    def _extra_check_fields(self, response: httpx.Response | None) -> dict[str, Any]:
        if response is not None:
            models = [m["name"] for m in response.json().get("models", [])]
            return {"ollamaModels": models}
        return {"ollamaModels": None}

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        base_url = config.custom_base_url or self.DEFAULT_BASE_URL
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=120.0,
        )

    async def _call_llm(
        self,
        system: str,
        user: str,
        json_mode: bool = True,
    ) -> dict[str, Any]:
        model = self.config.model or self.default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": build_messages(system, user),
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        response = await safe_post(self.client, "/api/chat", payload)
        data = response.json()
        text = data["message"]["content"]
        return extract_json(text)

    async def list_models(self) -> list[str]:
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return sorted(models)
        except Exception as e:
            print(f"Failed to fetch models from Ollama: {e}")
            return []
