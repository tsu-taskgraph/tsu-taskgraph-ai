from pydantic import BaseModel, Field
from app.schemas.common import ProviderConfig


class ProviderCheckRequest(BaseModel):
    provider_config: ProviderConfig = Field(..., alias="providerConfig")

    model_config = {"populate_by_name": True}


class ProviderCheckResponse(BaseModel):
    provider: str
    available: bool
    latency_ms: int | None = Field(None, alias="latencyMs", ge=0)
    error: str | None = None
    ollama_models: list[str] | None = Field(None, alias="ollamaModels")

    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
