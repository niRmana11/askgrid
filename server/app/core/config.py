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
    session_ttl_minutes: int = 60
    session_storage_dir: str = "/tmp/askgrid_sessions"
    gemini_api_key: str = ""
    gemini_models: str = (
        "gemini-3.5-flash-lite,gemini-3.1-flash-lite,"
        "gemini-3.5-flash,gemini-3.6-flash,gemini-3.7-flash"
    )
    ai_timeout_seconds: float = 25.0
    ai_circuit_cooldown_seconds: int = 120
    max_concurrent_analyses: int = 2

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Split comma-separated CORS origins into a clean list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def gemini_model_list(self) -> list[str]:
        """Parse comma-separated Gemini fallback models in priority order."""
        return [m.strip() for m in self.gemini_models.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()
