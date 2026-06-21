from typing import Any
from pydantic import BaseModel, Field

AiProviderType = str

PROVIDER_CHOICES = ["gemini", "openai", "anthropic", "groq", "mistral", "ollama"]


class ProviderDirectoryEntry(BaseModel):
    default_model: str = Field(..., alias="defaultModel")
    supported_models: list[str] = Field(..., alias="supportedModels")

    model_config = {"populate_by_name": True}


class ProviderConfig(BaseModel):
    provider: str = Field(..., pattern=r"^(gemini|openai|anthropic|groq|mistral|ollama)$")
    api_key: str | None = Field(None, alias="apiKey")
    model: str | None = None
    custom_base_url: str | None = Field(None, alias="customBaseUrl")

    model_config = {"populate_by_name": True}


TechStack = list[str]
