from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import router as api_router
from app.config import get_settings
from app.core.exceptions import build_error_response, validation_exception_handler


def create_app() -> FastAPI:
    settings = get_settings()

    fastapi_app = FastAPI(
        title="TaskGraph AI Service Bridge",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        servers=[
            {"url": "http://localhost:8000", "description": "Local development"},
            {"url": "http://ai-service:8000", "description": "Docker internal"},
        ],
    )

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    # noinspection PyTypeChecker
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @fastapi_app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(_request, exc):  # noqa: ANN001
        body = build_error_response(
            error="HTTPException",
            message=exc.detail,
        )
        return JSONResponse(content=body, status_code=exc.status_code)

    @fastapi_app.exception_handler(RequestValidationError)
    async def validation_exc_handler(_request, exc):
        return await validation_exception_handler(_request, exc)

    fastapi_app.include_router(api_router)
    return fastapi_app


app = create_app()


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "TaskGraph AI Service Bridge"}
