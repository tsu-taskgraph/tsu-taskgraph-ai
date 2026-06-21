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
