from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.schemas.common import AiProviderType


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: str | None = None
    provider: AiProviderType | None = None
    provider_http_status: int | None = Field(None, alias="providerHttpStatus")
    timestamp: str

    model_config = {"populate_by_name": True}


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
    from starlette.exceptions import HTTPException as StarletteHTTPException

    if isinstance(exc, StarletteHTTPException):
        if isinstance(exc.detail, dict):
            body = build_error_response(
                error=exc.detail.get("error", "HTTPException"),
                message=exc.detail.get("message", "An error occurred"),
                detail=exc.detail.get("detail"),
                provider=exc.detail.get("provider"),
                provider_http_status=exc.detail.get("providerHttpStatus"),
            )
        else:
            body = build_error_response(
                error="HTTPException",
                message=str(exc.detail),
            )
        return JSONResponse(status_code=exc.status_code, content=body)
    raise exc


async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    body = build_error_response(
        error="InternalServerError",
        message=str(exc),
        detail="An unexpected internal server error occurred."
    )
    return JSONResponse(status_code=500, content=body)


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    body = build_error_response(
        error="ValidationError",
        message="Request validation failed",
        detail=str(exc.errors()),
    )
    return JSONResponse(status_code=422, content=body)
