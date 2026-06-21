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


def _normalize_category(category: Any) -> str:
    valid_categories = {"BACKEND", "FRONTEND", "DEVOPS", "TESTING", "DOCUMENTATION", "DESIGN", "OTHER"}
    if category and isinstance(category, str):
        category_upper = category.upper().strip()
        if category_upper in valid_categories:
            return category_upper
    return "OTHER"


def _normalize_hours(est_hours: Any, ai_estimate: bool) -> float | None:
    if not ai_estimate:
        return None
    if est_hours is not None:
        try:
            val = float(est_hours)
            return val if val >= 0 else 0.0
        except (ValueError, TypeError):
            return 4.0
    return 4.0


def _clean_nodes(nodes: Any, existing_ids: set[str], ai_estimate: bool, prefix: str) -> list[dict[str, Any]]:
    if not isinstance(nodes, list):
        return []

    cleaned_nodes = []
    used_ids = set(existing_ids)

    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue

        temp_id = node.get("tempId") or node.get("temp_id")
        title = node.get("title")

        if not title:
            continue

        if not temp_id or not isinstance(temp_id, str):
            temp_id = f"{prefix}_{idx + 1}"

        orig_temp_id = temp_id
        counter = 1
        while temp_id in used_ids:
            temp_id = f"{orig_temp_id}_{counter}"
            counter += 1

        used_ids.add(temp_id)

        cleaned_node = {
            "tempId": temp_id,
            "title": str(title).strip(),
            "description": node.get("description"),
            "category": _normalize_category(node.get("category")),
        }

        est_hours = _normalize_hours(node.get("estimatedHours") or node.get("estimated_hours"), ai_estimate)
        if est_hours is not None:
            cleaned_node["estimatedHours"] = est_hours

        cleaned_nodes.append(cleaned_node)

    return cleaned_nodes


def _clean_edges(
    edges: Any,
    allowed_ids: set[str],
    src_keys: list[str],
    tgt_keys: list[str],
    out_src: str,
    out_tgt: str
) -> list[dict[str, str]]:
    if not isinstance(edges, list):
        return []

    cleaned_edges = []
    seen = set()

    for edge in edges:
        if not isinstance(edge, dict):
            continue

        src = next((edge.get(k) for k in src_keys if edge.get(k)), None)
        tgt = next((edge.get(k) for k in tgt_keys if edge.get(k)), None)

        if not src or not tgt:
            continue

        src = str(src).strip()
        tgt = str(tgt).strip()

        if src not in allowed_ids or tgt not in allowed_ids or src == tgt:
            continue

        edge_key = (src, tgt)
        if edge_key in seen:
            continue

        seen.add(edge_key)
        cleaned_edges.append({
            out_src: src,
            out_tgt: tgt
        })

    return cleaned_edges


def _filter_and_break_cycles(
    new_edges: list[dict[str, str]],
    all_nodes: set[str],
    source_key: str,
    target_key: str,
    base_edges: list[tuple[str, str]] = None
) -> list[dict[str, str]]:
    temp_adj = {nid: [] for nid in all_nodes}

    if base_edges:
        for src, tgt in base_edges:
            if src in temp_adj and tgt in temp_adj:
                temp_adj[src].append(tgt)

    final_new_edges = []

    for edge in new_edges:
        src = edge.get(source_key)
        tgt = edge.get(target_key)
        if not src or not tgt or src not in temp_adj or tgt not in temp_adj:
            continue

        temp_adj[src].append(tgt)

        visited = {nid: 0 for nid in all_nodes}
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

        for nid in all_nodes:
            if visited[nid] == 0:
                if check_cycle(nid):
                    cycle_found = True
                    break

        if cycle_found:
            temp_adj[src].remove(tgt)
        else:
            final_new_edges.append(edge)

    return final_new_edges


def validate_and_clean_skeleton(result: dict[str, Any], ai_estimate: bool = True) -> dict[str, Any]:
    cleaned_nodes = _clean_nodes(result.get("nodes"), set(), ai_estimate, "node")
    node_ids = {n["tempId"] for n in cleaned_nodes}

    src_keys = ["sourceTempId", "source_temp_id"]
    tgt_keys = ["targetTempId", "target_temp_id"]

    cleaned_edges = _clean_edges(result.get("edges"), node_ids, src_keys, tgt_keys, "sourceTempId", "targetTempId")

    final_edges = _filter_and_break_cycles(
        cleaned_edges,
        node_ids,
        "sourceTempId",
        "targetTempId"
    )

    return {
        "nodes": cleaned_nodes,
        "edges": final_edges
    }


def validate_and_clean_mutation(result: dict[str, Any], current_graph: dict[str, Any], ai_estimate: bool = True)\
        -> dict[str, Any]:
    existing_nodes = current_graph.get("nodes", []) if isinstance(current_graph, dict) else []
    existing_edges = current_graph.get("edges", []) if isinstance(current_graph, dict) else []

    existing_node_ids = set()
    for n in existing_nodes:
        nid = n.get("id") or n.get("tempId") or n.get("temp_id")
        if nid:
            existing_node_ids.add(str(nid).strip())

    cleaned_new_nodes = _clean_nodes(result.get("newNodes") or result.get("new_nodes"), existing_node_ids, ai_estimate,
                                     "new_node")
    new_node_ids = {n["tempId"] for n in cleaned_new_nodes}

    all_allowed_ids = existing_node_ids.union(new_node_ids)
    src_keys = ["sourceTempIdOrUuid", "source_temp_id_or_uuid", "sourceTempId", "sourceTaskId"]
    tgt_keys = ["targetTempIdOrUuid", "target_temp_id_or_uuid", "targetTempId", "targetTaskId"]

    cleaned_new_edges = _clean_edges(
        result.get("newEdges") or result.get("new_edges"),
        all_allowed_ids,
        src_keys,
        tgt_keys,
        "sourceTempIdOrUuid",
        "targetTempIdOrUuid"
    )

    base_edges = []
    for e in existing_edges:
        src = e.get("sourceTaskId") or e.get("source_task_id") or e.get("sourceTempId")
        tgt = e.get("targetTaskId") or e.get("target_task_id") or e.get("targetTempId")
        if src and tgt:
            base_edges.append((str(src).strip(), str(tgt).strip()))

    final_new_edges = _filter_and_break_cycles(
        cleaned_new_edges,
        all_allowed_ids,
        "sourceTempIdOrUuid",
        "targetTempIdOrUuid",
        base_edges
    )

    recalc_hours = result.get("recalculatedTotalHours") or result.get("recalculated_total_hours")
    if recalc_hours is not None:
        try:
            recalc_hours = float(recalc_hours)
        except (ValueError, TypeError):
            recalc_hours = None

    return {
        "newNodes": cleaned_new_nodes,
        "newEdges": final_new_edges,
        "recalculatedTotalHours": recalc_hours,
        "reasoning": result.get("reasoning")
    }
