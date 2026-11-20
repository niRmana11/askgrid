from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "AskGrid API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    allowed_origins: str = "http://localhost:5173"
    max_upload_size_mb: int = 10
    max_rows: int = 100_000
    max_columns: int = 50

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Split comma-separated CORS origins into a clean list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()
