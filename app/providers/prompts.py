from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Prompt:
    system: str
    user_template: str


SKELETON = Prompt(
    system=(
        "You are a technical lead. Generate a task graph skeleton for a software project. "
        "Return a JSON object with fields: nodes and edges."
    ),
    user_template=(
        "Project: {projectName}\n"
        "Tech stack: {techStack}\n"
        "Description: {description}"
    ),
)

ENRICH_TASK = Prompt(
    system=(
        "You are a technical mentor. Enrich a task. Return JSON with checklist, pitfalls, links, "
        "rawMarkdown, wikiDraft."
    ),
    user_template=(
        "Task: {taskTitle}\n"
        "Description: {taskDescription}"
    ),
)

MUTATE_GRAPH = Prompt(
    system=(
        "You are a technical lead. Return a JSON patch with newNodes, newEdges, "
        "recalculatedTotalHours, reasoning."
    ),
    user_template=(
        "Request: {prompt}\n"
        "Current graph: {currentGraph}"
    ),
)

SMART_RECOVERY = Prompt(
    system=(
        "You are a technical lead. Fix a cyclic patch. Return JSON with newNodes, newEdges, "
        "recalculatedTotalHours, reasoning."
    ),
    user_template=(
        "Cycle nodes: {cycleNodes}\n"
        "Failed patch: {failedMutation}"
    ),
)

DIAGRAMS = Prompt(
    system=(
        "You are a software architect. Generate Mermaid diagrams. Return JSON with "
        "c4Code, sequenceCode, classCode."
    ),
    user_template=(
        "Project: {projectName}\n"
        "Nodes: {nodes}\n"
        "Edges: {edges}"
    ),
)

WIKI = Prompt(
    system=(
        "You are a technical writer. Generate a Wiki page in Markdown. "
        "Return JSON with title and content."
    ),
    user_template=(
        "Task: {taskTitle}\n"
        "Description: {taskDescription}"
    ),
)

PROMPTS: dict[str, Prompt] = {
    "skeleton": SKELETON,
    "enrich_task": ENRICH_TASK,
    "mutate_graph": MUTATE_GRAPH,
    "smart_recovery": SMART_RECOVERY,
    "diagrams": DIAGRAMS,
    "wiki": WIKI,
}


def format_user(template: str, prompt_data: dict[str, Any]) -> str:
    return template.format_map(_FlattenDict(prompt_data))


class _FlattenDict(dict[str, Any]):

    def __getitem__(self, key: str) -> Any:  # type: ignore[override]
        if "." in key:
            obj: Any = self
            for part in key.split("."):
                if isinstance(obj, dict):
                    obj = obj[part]
                else:
                    return ""
            return obj
        try:
            return super().__getitem__(key)
        except KeyError:
            return ""


def _prepare_enrich_context(prompt_data: dict[str, Any]) -> dict[str, Any]:
    task = prompt_data.get("task", {})
    ctx = dict(prompt_data)
    ctx["taskTitle"] = task.get("taskTitle", "")
    ctx["taskDescription"] = task.get("taskDescription", "")
    return ctx


def _prepare_wiki_context(prompt_data: dict[str, Any]) -> dict[str, Any]:
    task = prompt_data.get("task", {})
    ctx = dict(prompt_data)
    ctx["taskTitle"] = task.get("taskTitle", "")
    ctx["taskDescription"] = task.get("taskDescription", "")
    return ctx


def _prepare_skeleton_context(prompt_data: dict[str, Any]) -> dict[str, Any]:
    ctx = dict(prompt_data)
    tech_stack = ctx.get("techStack", [])
    if isinstance(tech_stack, list):
        ctx["techStack"] = ", ".join(tech_stack)
    return ctx


_CONTEXT_HOOKS: dict[str, Any] = {
    "skeleton": _prepare_skeleton_context,
    "enrich_task": _prepare_enrich_context,
    "wiki": _prepare_wiki_context,
}


def build_prompt(action: str, prompt_data: dict[str, Any]) -> tuple[str, str]:
    prompt = PROMPTS[action]
    hook = _CONTEXT_HOOKS.get(action)
    ctx = hook(prompt_data) if hook else dict(prompt_data)
    return prompt.system, format_user(prompt.user_template, ctx)
