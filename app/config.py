from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TaskGraph AI Service Bridge"
    app_version: str = "1.0.0"
    debug: bool = False

    internal_secret: str

    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
