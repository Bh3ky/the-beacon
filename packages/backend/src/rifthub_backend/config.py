from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

_DOTENV_LOADED = False


class ConfigError(ValueError):
    """Raised when required application configuration is missing."""


def _load_dotenv() -> None:
    global _DOTENV_LOADED

    if _DOTENV_LOADED:
        return

    dotenv_path = find_dotenv(filename=".env", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=False)
    else:
        repo_dotenv = Path(__file__).resolve().parents[4] / ".env"
        if repo_dotenv.exists():
            load_dotenv(dotenv_path=repo_dotenv, override=False)

    _DOTENV_LOADED = True


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default

    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ConfigError(f"Missing required environment variable: {name}")

    return value


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = ""
    migration_database_url: str = ""
    sql_echo: bool = False


def get_settings() -> Settings:
    _load_dotenv()
    database_url = _required_env("RIFTHUB_DATABASE_URL")

    return Settings(
        environment=os.getenv("RIFTHUB_ENV", "development"),
        log_level=os.getenv("RIFTHUB_LOG_LEVEL", "INFO").upper(),
        api_host=os.getenv("RIFTHUB_API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("RIFTHUB_API_PORT", "8000")),
        database_url=database_url,
        migration_database_url=os.getenv(
            "RIFTHUB_MIGRATION_DATABASE_URL",
            database_url,
        ),
        sql_echo=_env_bool("RIFTHUB_SQL_ECHO", False),
    )
