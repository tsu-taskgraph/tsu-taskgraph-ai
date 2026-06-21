from pydantic import BaseModel, Field

from app.schemas.common import ProviderConfig, TechStack


class WikiTaskLink(BaseModel):
    title: str
    url: str


class WikiTaskContext(BaseModel):
    task_id: str = Field(..., alias="taskId")
    task_title: str = Field(..., alias="taskTitle")
    task_description: str | None = Field(None, alias="taskDescription")
    category: str | None = Field(
        None,
        pattern=r"^(BACKEND|FRONTEND|DEVOPS|TESTING|DOCUMENTATION|DESIGN|OTHER)$",
    )
    estimated_hours: float | None = Field(None, alias="estimatedHours", ge=0)
    predecessor_titles: list[str] = Field(default=[], alias="predecessorTitles")
    successor_titles: list[str] = Field(default=[], alias="successorTitles")
    checklist: list[str] = []
    pitfalls: list[str] = []
    links: list[WikiTaskLink] = []

    model_config = {"populate_by_name": True}


class GenerateWikiRequest(BaseModel):
    project_name: str = Field(..., alias="projectName")
    tech_stack: TechStack = Field(..., alias="techStack")
    task: WikiTaskContext
    existing_content: str | None = Field(None, alias="existingContent")
    provider_config: ProviderConfig = Field(..., alias="providerConfig")

    model_config = {"populate_by_name": True}


class GenerateWikiResponse(BaseModel):
    title: str
    content: str
    model_used: str | None = Field(None, alias="modelUsed")
    provider: str | None = None

    model_config = {"populate_by_name": True}
