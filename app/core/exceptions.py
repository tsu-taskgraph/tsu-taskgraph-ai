from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.schemas.common import AiProviderType


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: str | None = None
    provider: AiProviderType | None = None
    provider_http_status: int | None = None
    timestamp: str


def build_error_response(
    error: str,
    message: str,
    detail: str | None = None,
    provider: AiProviderType | None = None,
    provider_http_status: int | None = None,
) -> dict[str, Any]:
    return {
        "error": error,
        "message": message,
        "detail": detail,
        "provider": provider,
        "providerHttpStatus": provider_http_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        body = build_error_response(
            error="HTTPException",
            message=str(exc.detail),
        )
        return JSONResponse(status_code=exc.status_code, content=body)
    raise exc


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    body = build_error_response(
        error="ValidationError",
        message="Request validation failed",
        detail=str(exc.errors()),
    )
    return JSONResponse(status_code=422, content=body)
