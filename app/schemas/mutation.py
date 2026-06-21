from pydantic import BaseModel, Field

from app.schemas.common import ProviderConfig, TechStack
from app.schemas.skeleton import SkeletonNode


class GraphNode(BaseModel):
    id: str
    title: str
    status: str = Field(..., pattern=r"^(LOCKED|AVAILABLE|IN_PROGRESS|COMPLETED|SKIPPED)$")
    estimated_hours: float | None = Field(None, alias="estimatedHours", ge=0)

    model_config = {"populate_by_name": True}


class GraphEdge(BaseModel):
    source_task_id: str = Field(..., alias="sourceTaskId")
    target_task_id: str = Field(..., alias="targetTaskId")

    model_config = {"populate_by_name": True}


class GraphSnapshot(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class MutateGraphRequest(BaseModel):
    current_graph: GraphSnapshot = Field(..., alias="currentGraph")
    prompt: str
    project_name: str = Field(..., alias="projectName")
    tech_stack: TechStack = Field(..., alias="techStack")
    ai_estimate: bool = Field(default=True, alias="aiEstimate")
    provider_config: ProviderConfig = Field(..., alias="providerConfig")

    model_config = {"populate_by_name": True}


class NewMutationEdge(BaseModel):
    source_temp_id_or_uuid: str = Field(..., alias="sourceTempIdOrUuid")
    target_temp_id_or_uuid: str = Field(..., alias="targetTempIdOrUuid")

    model_config = {"populate_by_name": True}


class MutationPatch(BaseModel):
    new_nodes: list[SkeletonNode] = Field(default=[], alias="newNodes")
    new_edges: list[NewMutationEdge] = Field(default=[], alias="newEdges")
    recalculated_total_hours: float | None = Field(None, alias="recalculatedTotalHours")
    reasoning: str | None = None

    model_config = {"populate_by_name": True}


class MutateGraphResponse(BaseModel):
    patch: MutationPatch
    model_used: str | None = Field(None, alias="modelUsed")
    provider: str | None = None

    model_config = {"populate_by_name": True}
