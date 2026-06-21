from pydantic import BaseModel, Field


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
