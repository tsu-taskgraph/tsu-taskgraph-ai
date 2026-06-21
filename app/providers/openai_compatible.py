from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.utils import (
    build_messages,
    extract_json,
    map_common_params,
    safe_post,
)
from app.schemas.common import ProviderConfig


class OpenAICompatibleProvider(BaseProvider):
    BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o"

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

    def build_params(self, settings: dict[str, Any] | None) -> dict[str, Any]:
        return map_common_params(settings)

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
        settings_dict = (
            self.config.settings.model_dump(by_alias=True) if self.config.settings else None
        )
        payload.update(self.build_params(settings_dict))
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = await safe_post(self.client, "/chat/completions", payload)
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return extract_json(content)
