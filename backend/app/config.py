import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _load_backend_env_file() -> None:
    """Load backend/.env regardless of current working directory."""
    backend_root = Path(__file__).resolve().parents[1]
    env_path = backend_root / ".env"
    load_dotenv(env_path, override=False)


def _as_bool(value: str | None, default: bool = False) -> bool:


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


_load_backend_env_file()


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("ENV", "development")
    enable_api_docs: bool = _as_bool(os.getenv("ENABLE_API_DOCS"), False)
    run_legacy_startup_migrations: bool = _as_bool(os.getenv("RUN_LEGACY_STARTUP_MIGRATIONS"), False)
    run_create_all_in_dev: bool = _as_bool(os.getenv("RUN_CREATE_ALL_IN_DEV"), False)
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "")
    database_url: str | None = os.getenv("DATABASE_URL")
    jwt_secret_key: str | None = os.getenv("JWT_SECRET_KEY")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    debug: bool = _as_bool(os.getenv("DEBUG"), False)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    sql_log_level: str = os.getenv("SQL_LOG_LEVEL", "WARNING")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "5"))
    db_pool_recycle_seconds: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))
    db_pool_timeout_seconds: int = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
