import json
import re
from typing import Any, NoReturn

import httpx
from fastapi import HTTPException, status


class ProviderError(Exception):
    def __init__(self, message: str, provider_http_status: int | None = None):
        super().__init__(message)
        self.provider_http_status = provider_http_status


def build_messages(system: str, user: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def extract_json(text: str) -> dict[str, Any]:
    code_block = re.search(r"```(?:json)?\s*(\{.*?})\s*```", text, re.DOTALL)
    if code_block:
        candidate = code_block.group(1)
    else:
        match = re.search(r"(\{.*})", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response")
        candidate = match.group(1)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e


def handle_provider_error(message: str, status_code: int | None = None) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "error": "ProviderError",
            "message": message,
            "providerHttpStatus": status_code,
        },
    )


async def safe_post(
    client: httpx.AsyncClient,
    url: str,
    payload: dict[str, Any],
) -> httpx.Response:
    try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        handle_provider_error(str(e), e.response.status_code)
    except httpx.RequestError as e:
        handle_provider_error(str(e))


def map_common_params(settings: dict[str, Any] | None) -> dict[str, Any]:
    if not settings:
        return {}
    params: dict[str, Any] = {}
    if settings.get("temperature") is not None:
        params["temperature"] = settings["temperature"]
    if settings.get("maxTokens") is not None:
        params["max_tokens"] = settings["maxTokens"]
    return params


def validate_and_clean_skeleton(result: dict[str, Any], ai_estimate: bool = True) -> dict[str, Any]:
    nodes = result.get("nodes", [])
    if not isinstance(nodes, list):
        nodes = []

    edges = result.get("edges", [])
    if not isinstance(edges, list):
        edges = []

    valid_categories = {"BACKEND", "FRONTEND", "DEVOPS", "TESTING", "DOCUMENTATION", "DESIGN", "OTHER"}

    cleaned_nodes = []
    node_ids = set()

    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue

        temp_id = node.get("tempId") or node.get("temp_id")
        title = node.get("title")

        if not title:
            continue

        if not temp_id or not isinstance(temp_id, str):
            temp_id = f"node_{idx + 1}"

        orig_temp_id = temp_id
        counter = 1
        while temp_id in node_ids:
            temp_id = f"{orig_temp_id}_{counter}"
            counter += 1

        node_ids.add(temp_id)

        category = node.get("category")
        if category and isinstance(category, str):
            category = category.upper().strip()
            if category not in valid_categories:
                category = "OTHER"
        else:
            category = "OTHER"

        est_hours = node.get("estimatedHours") or node.get("estimated_hours")
        if ai_estimate:
            if est_hours is not None:
                try:
                    est_hours = float(est_hours)
                    if est_hours < 0:
                        est_hours = 0.0
                except (ValueError, TypeError):
                    est_hours = 4.0
            else:
                est_hours = 4.0
        else:
            est_hours = None

        cleaned_node = {
            "tempId": temp_id,
            "title": str(title).strip(),
            "description": node.get("description"),
            "category": category,
        }
        if est_hours is not None:
            cleaned_node["estimatedHours"] = est_hours

        cleaned_nodes.append(cleaned_node)

    cleaned_edges = []
    seen_edges = set()

    for edge in edges:
        if not isinstance(edge, dict):
            continue

        src = edge.get("sourceTempId") or edge.get("source_temp_id") or edge.get("sourceTempIdOrUuid") or edge.get(
            "source_temp_id_or_uuid")
        tgt = edge.get("targetTempId") or edge.get("target_temp_id") or edge.get("targetTempIdOrUuid") or edge.get(
            "target_temp_id_or_uuid")

        if not src or not tgt:
            continue

        src = str(src).strip()
        tgt = str(tgt).strip()

        if src not in node_ids or tgt not in node_ids or src == tgt:
            continue

        edge_key = (src, tgt)
        if edge_key in seen_edges:
            continue

        seen_edges.add(edge_key)
        cleaned_edges.append({
            "sourceTempId": src,
            "targetTempId": tgt
        })

    adj = {nid: [] for nid in node_ids}
    for edge in cleaned_edges:
        adj[edge["sourceTempId"]].append(edge["targetTempId"])

    temp_adj = {nid: [] for nid in node_ids}
    final_edges = []

    for edge in cleaned_edges:
        src, tgt = edge["sourceTempId"], edge["targetTempId"]
        temp_adj[src].append(tgt)

        visited = {nid: 0 for nid in node_ids}
        cycle_found = False

        def check_cycle(u):
            visited[u] = 1
            for v in temp_adj[u]:
                if visited[v] == 1:
                    return True
                elif visited[v] == 0:
                    if check_cycle(v):
                        return True
            visited[u] = 2
            return False

        for nid in node_ids:
            if visited[nid] == 0:
                if check_cycle(nid):
                    cycle_found = True
                    break

        if cycle_found:
            temp_adj[src].remove(tgt)
        else:
            final_edges.append(edge)

    return {
        "nodes": cleaned_nodes,
        "edges": final_edges
    }