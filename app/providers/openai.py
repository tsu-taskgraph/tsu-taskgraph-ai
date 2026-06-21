from typing import Any

from app.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas.common import ProviderConfig


class OpenAIProvider(OpenAICompatibleProvider):
    BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-5.3-instant"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    def build_params(self, settings: dict[str, Any] | None) -> dict[str, Any]:
        params = super().build_params(settings)
        if settings:
            reasoning_effort = settings.get("reasoningEffort")
            if reasoning_effort and self.config.model and self.config.model.startswith("o"):
                params["reasoning_effort"] = reasoning_effort
                params.pop("temperature", None)
        return params
