from app.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas.common import ProviderConfig


class OpenAIProvider(OpenAICompatibleProvider):
    BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-5.3-instant"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
