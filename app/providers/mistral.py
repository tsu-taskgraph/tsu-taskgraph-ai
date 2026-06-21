from app.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas.common import ProviderConfig


class MistralProvider(OpenAICompatibleProvider):
    BASE_URL = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-large-latest"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
