from app.providers.anthropic_compatible import AnthropicCompatibleProvider
from app.schemas.common import ProviderConfig


class AnthropicProvider(AnthropicCompatibleProvider):
    BASE_URL = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-sonnet-4.6"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
