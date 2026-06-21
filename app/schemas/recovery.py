from pydantic import BaseModel, Field

from app.schemas.common import ProviderConfig, TechStack
from app.schemas.mutation import GraphSnapshot, MutationPatch


class SmartRecoveryRequest(BaseModel):
    current_graph: GraphSnapshot = Field(..., alias="currentGraph")
    failed_mutation: MutationPatch = Field(..., alias="failedMutation")
    cycle_nodes: list[str] = Field(..., alias="cycleNodes")
    project_name: str = Field(..., alias="projectName")
    tech_stack: TechStack = Field(..., alias="techStack")
    ai_estimate: bool = Field(default=True, alias="aiEstimate")
    provider_config: ProviderConfig = Field(..., alias="providerConfig")

    model_config = {"populate_by_name": True}


class SmartRecoveryResponse(BaseModel):
    fixed_patch: MutationPatch = Field(..., alias="fixedPatch")
    recovery_note: str = Field(..., alias="recoveryNote")
    model_used: str | None = Field(None, alias="modelUsed")
    provider: str | None = None

    model_config = {"populate_by_name": True}
