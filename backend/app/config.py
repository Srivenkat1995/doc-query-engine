from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Document Query Engine API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "sqlite:///./data/doc_query.db"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: str = "./uploads"
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DOC_QUERY_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance for the process."""

    return Settings()
