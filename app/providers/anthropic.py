from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.utils import (
    extract_json,
    safe_post,
)
from app.schemas.common import ProviderConfig


class AnthropicProvider(BaseProvider):
    BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4.6"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "x-api-key": config.api_key or "",
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def _call_llm(
        self,
        system: str,
        user: str,
        json_mode: bool = True,
    ) -> dict[str, Any]:
        model = self.config.model or self.default_model
        if json_mode:
            system = f"{system}\n\nAlways respond with a valid JSON object."

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }

        response = await safe_post(self.client, "/messages", payload)
        data = response.json()
        text = data["content"][0]["text"]
        return extract_json(text)

    async def list_models(self) -> list[str]:
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            return sorted(models)
        except Exception as e:
            print(f"Failed to fetch models from Anthropic: {e}")
            return []
