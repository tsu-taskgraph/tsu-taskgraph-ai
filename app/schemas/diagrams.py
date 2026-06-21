from pydantic import BaseModel, Field

from app.schemas.common import ProviderConfig, TechStack


class DiagramLink(BaseModel):
    title: str
    url: str


class DiagramNode(BaseModel):
    id: str
    title: str
    description: str | None = None
    category: str | None = Field(
        None,
        pattern=r"^(BACKEND|FRONTEND|DEVOPS|TESTING|DOCUMENTATION|DESIGN|OTHER)$",
    )
    status: str = Field(..., pattern=r"^(LOCKED|AVAILABLE|IN_PROGRESS|COMPLETED|SKIPPED)$")
    layer: int
    checklist: list[str] = []
    links: list[DiagramLink] = []


class DiagramEdge(BaseModel):
    source_task_id: str = Field(..., alias="sourceTaskId")
    target_task_id: str = Field(..., alias="targetTaskId")

    model_config = {"populate_by_name": True}


class DiagramRequest(BaseModel):
    nodes: list[DiagramNode]
    edges: list[DiagramEdge]
    project_name: str = Field(..., alias="projectName")
    tech_stack: TechStack = Field(..., alias="techStack")
    provider_config: ProviderConfig = Field(..., alias="providerConfig")
    requested_diagrams: list[str] = Field(
        default=["c4", "sequence", "class"],
        alias="requestedDiagrams",
    )

    model_config = {"populate_by_name": True}


class DiagramResponse(BaseModel):
    c4_code: str | None = Field(None, alias="c4Code")
    sequence_code: str | None = Field(None, alias="sequenceCode")
    class_code: str | None = Field(None, alias="classCode")
    model_used: str | None = Field(None, alias="modelUsed")
    provider: str | None = None

    model_config = {"populate_by_name": True}
