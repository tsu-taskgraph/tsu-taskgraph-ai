from app.api.router import router as api_router
from app.config import get_settings
from app.core.exceptions import validation_exception_handler
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException


def create_app() -> FastAPI:
    settings = get_settings()

    fastapi_app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/api/v1/ai/docs",
        redoc_url="/api/v1/ai/redoc",
        openapi_url="/api/v1/ai/openapi.json",
        servers=[
            {"url": "/", "description": "Production via nginx"},
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
        from app.core.exceptions import http_exception_handler
        return await http_exception_handler(_request, exc)

    @fastapi_app.exception_handler(RequestValidationError)
    async def validation_exc_handler(_request, exc):
        return await validation_exception_handler(_request, exc)

    @fastapi_app.exception_handler(Exception)
    async def general_exception_handler(_request, exc):
        from app.core.exceptions import global_exception_handler
        return await global_exception_handler(_request, exc)

    fastapi_app.include_router(api_router)

    from fastapi.openapi.utils import get_openapi

    def custom_openapi():
        if fastapi_app.openapi_schema:
            return fastapi_app.openapi_schema

        openapi_schema = get_openapi(
            title=fastapi_app.title,
            version=fastapi_app.version,
            routes=fastapi_app.routes,
            servers=fastapi_app.servers,
        )

        for path in openapi_schema.get("paths", {}).values():
            for method in path.values():
                if "responses" in method and "422" in method["responses"]:
                    response_422 = method["responses"]["422"]
                    response_422["description"] = ("Unprocessable Entity - Ошибка валидации структуры или невалидный "
                                                   "ответ ИИ")
                    if "content" in response_422 and "application/json" in response_422["content"]:
                        response_422["content"]["application/json"]["schema"] = {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }

        components = openapi_schema.get("components", {})
        if "schemas" in components:
            components["schemas"].pop("HTTPValidationError", None)
            components["schemas"].pop("ValidationError", None)

        fastapi_app.openapi_schema = openapi_schema
        return fastapi_app.openapi_schema

    fastapi_app.openapi = custom_openapi
    return fastapi_app


app = create_app()


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    settings = get_settings()
    return {"message": settings.app_name}
