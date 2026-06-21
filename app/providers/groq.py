from typing import Any

from app.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas.common import ProviderConfig


class GroqProvider(OpenAICompatibleProvider):
    BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    def _build_params(self, settings: dict[str, Any] | None) -> dict[str, Any]:
        params = super()._build_params(settings)
        if settings and settings.get("groqReasoningFormat"):
            params["reasoning_format"] = settings["groqReasoningFormat"]
        return params
