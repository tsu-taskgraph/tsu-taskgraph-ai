from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.utils import (
    extract_json,
    safe_post,
)
from app.schemas.common import ProviderConfig


def _build_generation_config(settings: dict[str, Any] | None) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if not settings:
        return config
    if settings.get("temperature") is not None:
        config["temperature"] = settings["temperature"]
    if settings.get("maxTokens") is not None:
        config["maxOutputTokens"] = settings["maxTokens"]
    if settings.get("thinkingBudget") is not None:
        config["thinkingConfig"] = {"thinkingBudget": settings["thinkingBudget"]}
    return config


def _build_tools(settings: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if settings and settings.get("enableWebSearch"):
        return [{"google_search": {}}]
    return None


class GeminiProvider(BaseProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def default_model(self) -> str:
        return "gemini-3.5-flash"

    @property
    def check_url(self) -> str:
        return f"/models?key={self.config.api_key}"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=60.0,
        )

    async def _call_llm(
        self,
        system: str,
        user: str,
        json_mode: bool = True,
    ) -> dict[str, Any]:
        model = self.config.model or self.default_model
        settings_dict = (
            self.config.settings.model_dump(by_alias=True) if self.config.settings else None
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system}\n\n{user}"}],
                }
            ],
            "generationConfig": _build_generation_config(settings_dict),
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        tools = _build_tools(settings_dict)
        if tools:
            payload["tools"] = tools

        url = f"/models/{model}:generateContent?key={self.config.api_key}"
        response = await safe_post(self.client, url, payload)
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return extract_json(text)

    async def list_models(self) -> list[str]:
        try:
            url = f"/models?key={self.config.api_key}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                if name.startswith("models/"):
                    name = name[len("models/"):]
                models.append(name)
            return sorted(models)
        except Exception as e:
            print(f"Failed to fetch models from Gemini: {e}")
            return []
