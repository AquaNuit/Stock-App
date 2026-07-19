"""Application settings — single source of configuration truth (see docs/deployment.md §3).

All values are overridable via environment variables or a local `.env` file.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Env vars map 1:1, case-insensitive."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    env: str = "dev"
    app_name: str = "StockSense AI"
    version: str = "0.1.0"
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./stocksense.db"
    db_pool_size: int = 5

    # Cache / rate limiting
    redis_url: str = ""
    rate_limit_per_minute: int = 120
    cache_ttl_quote_s: int = 60
    cache_ttl_history_s: int = 60 * 60 * 6
    cache_ttl_search_s: int = 60 * 60 * 24
    cache_ttl_overview_s: int = 60

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Providers
    seed_fallback: bool = True
    provider_timeout_s: float = 8.0
    nse_enabled: bool = True

    # ML
    train_max_range_years: int = 10
    max_concurrent_trains: int = 4

    # Scheduler
    scheduler_enabled: bool = True

    # Artifacts (roadmap R2.9)
    model_artifacts_bucket: str = ""

    @field_validator("log_level")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.env.lower() == "prod"

    @property
    def use_redis(self) -> bool:
        return bool(self.redis_url.strip())


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (one parse per process)."""
    return Settings()
