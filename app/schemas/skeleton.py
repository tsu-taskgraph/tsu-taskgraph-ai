from pydantic import BaseModel, Field

from app.schemas.common import ProviderConfig, TechStack


class GenerateSkeletonRequest(BaseModel):
    project_name: str = Field(..., alias="projectName")
    tech_stack: TechStack = Field(..., alias="techStack")
    description: str
    team_size: int = Field(default=1, alias="teamSize", ge=1)
    ai_estimate: bool = Field(default=True, alias="aiEstimate")
    provider_config: ProviderConfig = Field(..., alias="providerConfig")

    model_config = {"populate_by_name": True}


class SkeletonNode(BaseModel):
    temp_id: str = Field(..., alias="tempId")
    title: str
    description: str | None = None
    category: str | None = Field(
        None,
        pattern=r"^(BACKEND|FRONTEND|DEVOPS|TESTING|DOCUMENTATION|DESIGN|OTHER)$",
    )
    estimated_hours: float | None = Field(None, alias="estimatedHours", ge=0)

    model_config = {"populate_by_name": True}


class SkeletonEdge(BaseModel):
    source_temp_id: str = Field(..., alias="sourceTempId")
    target_temp_id: str = Field(..., alias="targetTempId")

    model_config = {"populate_by_name": True}


class GenerateSkeletonResponse(BaseModel):
    nodes: list[SkeletonNode]
    edges: list[SkeletonEdge]
    total_estimated_hours: float | None = Field(None, alias="totalEstimatedHours")
    model_used: str | None = Field(None, alias="modelUsed")
    provider: str | None = None
    prompt_tokens: int | None = Field(None, alias="promptTokens")
    completion_tokens: int | None = Field(None, alias="completionTokens")
    thinking_tokens: int | None = Field(None, alias="thinkingTokens")

    model_config = {"populate_by_name": True}
