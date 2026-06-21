from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import router as api_router
from app.config import get_settings
from app.core.exceptions import build_error_response, validation_exception_handler


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
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

    from fastapi.responses import JSONResponse

    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(request, exc):  # noqa: ANN001
        body = build_error_response(
            error="HTTPException",
            message=exc.detail,
        )
        return JSONResponse(content=body, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exc_handler(request, exc):  # noqa: ANN001
        return await validation_exception_handler(request, exc)

    app.include_router(api_router)
    return app


app = create_app()


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "TaskGraph AI Service Bridge"}


@app.get("/hello/{name}")
async def say_hello(name: str) -> dict[str, str]:
    return {"message": f"Hello {name}"}
