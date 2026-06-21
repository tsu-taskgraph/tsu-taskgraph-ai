from pydantic import BaseModel, Field

from app.schemas.common import ProviderConfig, TechStack


class TaskContext(BaseModel):
    task_id: str = Field(..., alias="taskId")
    task_title: str = Field(..., alias="taskTitle")
    task_description: str | None = Field(None, alias="taskDescription")
    category: str | None = Field(
        None,
        pattern=r"^(BACKEND|FRONTEND|DEVOPS|TESTING|DOCUMENTATION|DESIGN|OTHER)$",
    )
    predecessor_titles: list[str] = Field(default=[], alias="predecessorTitles")
    successor_titles: list[str] = Field(default=[], alias="successorTitles")
    estimated_hours: float | None = Field(None, alias="estimatedHours", ge=0)

    model_config = {"populate_by_name": True}


class EnrichTaskRequest(BaseModel):
    project_name: str = Field(..., alias="projectName")
    tech_stack: TechStack = Field(..., alias="techStack")
    task: TaskContext
    callback_url: str = Field(..., alias="callbackUrl")
    generate_wiki_draft: bool = Field(default=True, alias="generateWikiDraft")
    provider_config: ProviderConfig = Field(..., alias="providerConfig")

    model_config = {"populate_by_name": True}


class DocLink(BaseModel):
    title: str
    url: str


class EnrichTaskJobResponse(BaseModel):
    job_id: str = Field(..., alias="jobId")
    task_id: str = Field(..., alias="taskId")
    status: str = "QUEUED"
    estimated_seconds: int | None = Field(None, alias="estimatedSeconds", ge=0)

    model_config = {"populate_by_name": True}


class EnrichTaskResponse(BaseModel):
    task_id: str = Field(..., alias="taskId")
    checklist: list[str] = []
    pitfalls: list[str] = []
    links: list[DocLink] = []
    raw_markdown: str = Field(..., alias="rawMarkdown")
    wiki_draft: str | None = Field(None, alias="wikiDraft")
    model_used: str | None = Field(None, alias="modelUsed")
    provider: str | None = None

    model_config = {"populate_by_name": True}


class EnrichTaskCallback(BaseModel):
    job_id: str = Field(..., alias="jobId")
    task_id: str = Field(..., alias="taskId")
    status: str = Field(..., pattern=r"^(SUCCESS|FAILED)$")
    result: EnrichTaskResponse | None = None
    error: str | None = None
    provider_error: str | None = Field(None, alias="providerError")

    model_config = {"populate_by_name": True}
