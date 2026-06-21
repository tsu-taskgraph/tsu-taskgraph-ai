from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.utils import (
    build_messages,
    extract_json,
    safe_post,
)
from app.schemas.common import ProviderConfig


class OpenAICompatibleProvider(BaseProvider):
    BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-5.3-instant"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        base_url = config.custom_base_url or self.BASE_URL
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
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
        payload: dict[str, Any] = {
            "model": model,
            "messages": build_messages(system, user),
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = await safe_post(self.client, "/chat/completions", payload)
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return extract_json(content)

    async def list_models(self) -> list[str]:
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            return sorted(models)
        except Exception as e:
            print(f"Failed to fetch models from OpenAICompatible: {e}")
            return []
