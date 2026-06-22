from app.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas.common import ProviderConfig


class GroqProvider(OpenAICompatibleProvider):
    BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
