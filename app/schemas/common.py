from typing import Any
from pydantic import BaseModel, Field

AiProviderType = str

PROVIDER_CHOICES = ["gemini", "openai", "anthropic", "groq", "mistral", "ollama"]


class ProviderDirectoryEntry(BaseModel):
    default_model: str = Field(..., alias="defaultModel")
    supported_models: list[str] = Field(..., alias="supportedModels")
    supports_web_search: bool = Field(..., alias="supportsWebSearch")
    supports_extended_thinking: bool = Field(..., alias="supportsExtendedThinking")
    supports_reasoning_effort: bool = Field(..., alias="supportsReasoningEffort")
    settings_schema: dict[str, Any] = Field(..., alias="settingsSchema")

    model_config = {"populate_by_name": True}


class ProviderSettings(BaseModel):
    temperature: float | None = None
    max_tokens: int | None = Field(None, alias="maxTokens")

    # Gemini
    thinking_budget: int | None = Field(None, alias="thinkingBudget")
    enable_web_search: bool | None = Field(None, alias="enableWebSearch")

    # Anthropic
    extended_thinking: bool | None = Field(None, alias="extendedThinking")
    thinking_token_budget: int | None = Field(None, alias="thinkingTokenBudget")

    # OpenAI
    reasoning_effort: str | None = Field(None, alias="reasoningEffort")

    # Groq
    groq_reasoning_format: str | None = Field(None, alias="groqReasoningFormat")

    # Ollama
    ollama_num_ctx: int | None = Field(None, alias="ollamaNumCtx")
    ollama_num_gpu: int | None = Field(None, alias="ollamaNumGpu")

    model_config = {"populate_by_name": True}


class ProviderConfig(BaseModel):
    provider: str = Field(..., pattern=r"^(gemini|openai|anthropic|groq|mistral|ollama)$")
    api_key: str | None = Field(None, alias="apiKey")
    model: str | None = None
    custom_base_url: str | None = Field(None, alias="customBaseUrl")
    settings: ProviderSettings | None = None

    model_config = {"populate_by_name": True}


TechStack = list[str]
