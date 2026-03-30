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


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default

    return int(raw.strip())


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ConfigError(f"Missing required environment variable: {name}")

    return value


def _secret_env(name: str, *, environment: str) -> str:
    value = os.getenv(name)
    if value and value.strip():
        return value

    if environment in {"development", "test"}:
        return "dev-insecure-secret"

    raise ConfigError(f"Missing required environment variable: {name}")


def _env_csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default

    values = tuple(part.strip() for part in raw.split(",") if part.strip())
    return values or default


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = ""
    migration_database_url: str = ""
    sql_echo: bool = False
    app_secret: str = "dev-insecure-secret"
    session_cookie_name: str = "rifthub_session"
    csrf_cookie_name: str = "rifthub_csrf"
    session_idle_minutes: int = 30
    session_absolute_hours: int = 24
    session_touch_interval_minutes: int = 10
    verification_token_ttl_hours: int = 24
    verification_delivery_mode: str = "log"
    frontend_base_url: str = "http://localhost:3000"
    verification_from_email: str = "noreply@localhost"
    verification_smtp_host: str = "127.0.0.1"
    verification_smtp_port: int = 1025
    verification_smtp_starttls: bool = False
    resend_api_key: str = ""
    allowed_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")
    rate_limit_backend: str = "memory"
    redis_url: str = ""
    rate_limit_prefix: str = "rifthub:rate-limit"
    trusted_proxy_ips: tuple[str, ...] = ("127.0.0.1", "::1")
    ingestion_system_username: str = "rifthub_bot"
    ingestion_system_email: str = "ingestion-bot@localhost"


def get_settings() -> Settings:
    _load_dotenv()
    database_url = _required_env("RIFTHUB_DATABASE_URL")
    environment = os.getenv("RIFTHUB_ENV", "development")
    default_delivery_mode = "noop" if environment == "test" else "log"
    default_rate_limit_backend = "memory" if environment in {"development", "test"} else "redis"
    redis_url = os.getenv("RIFTHUB_REDIS_URL", "").strip()
    rate_limit_backend = os.getenv(
        "RIFTHUB_RATE_LIMIT_BACKEND",
        default_rate_limit_backend,
    ).strip().lower()
    default_trusted_proxy_ips = ("127.0.0.1", "::1") if environment in {"development", "test"} else ()

    if rate_limit_backend == "redis" and not redis_url:
        raise ConfigError("Missing required environment variable: RIFTHUB_REDIS_URL")

    return Settings(
        environment=environment,
        log_level=os.getenv("RIFTHUB_LOG_LEVEL", "INFO").upper(),
        api_host=os.getenv("RIFTHUB_API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("RIFTHUB_API_PORT", "8000")),
        database_url=database_url,
        migration_database_url=os.getenv(
            "RIFTHUB_MIGRATION_DATABASE_URL",
            database_url,
        ),
        sql_echo=_env_bool("RIFTHUB_SQL_ECHO", False),
        app_secret=_secret_env("RIFTHUB_APP_SECRET", environment=environment),
        session_cookie_name=os.getenv("RIFTHUB_SESSION_COOKIE_NAME", "rifthub_session"),
        csrf_cookie_name=os.getenv("RIFTHUB_CSRF_COOKIE_NAME", "rifthub_csrf"),
        session_idle_minutes=_env_int("RIFTHUB_SESSION_IDLE_MINUTES", 30),
        session_absolute_hours=_env_int("RIFTHUB_SESSION_ABSOLUTE_HOURS", 24),
        session_touch_interval_minutes=_env_int("RIFTHUB_SESSION_TOUCH_INTERVAL_MINUTES", 10),
        verification_token_ttl_hours=_env_int("RIFTHUB_VERIFICATION_TOKEN_TTL_HOURS", 24),
        verification_delivery_mode=os.getenv(
            "RIFTHUB_VERIFICATION_DELIVERY_MODE",
            default_delivery_mode,
        ).strip().lower(),
        frontend_base_url=os.getenv("RIFTHUB_FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/"),
        verification_from_email=os.getenv("RIFTHUB_VERIFICATION_FROM_EMAIL", "noreply@localhost"),
        verification_smtp_host=os.getenv("RIFTHUB_VERIFICATION_SMTP_HOST", "127.0.0.1"),
        verification_smtp_port=_env_int("RIFTHUB_VERIFICATION_SMTP_PORT", 1025),
        verification_smtp_starttls=_env_bool("RIFTHUB_VERIFICATION_SMTP_STARTTLS", False),
        resend_api_key=os.getenv("RIFTHUB_RESEND_API_KEY", "").strip(),
        allowed_origins=_env_csv(
            "RIFTHUB_ALLOWED_ORIGINS",
            ("http://localhost:3000", "http://127.0.0.1:3000"),
        ),
        rate_limit_backend=rate_limit_backend,
        redis_url=redis_url,
        rate_limit_prefix=os.getenv("RIFTHUB_RATE_LIMIT_PREFIX", "rifthub:rate-limit").strip()
        or "rifthub:rate-limit",
        trusted_proxy_ips=_env_csv(
            "RIFTHUB_TRUSTED_PROXY_IPS",
            default_trusted_proxy_ips,
        ),
        ingestion_system_username=os.getenv("RIFTHUB_INGESTION_SYSTEM_USERNAME", "rifthub_bot").strip()
        or "rifthub_bot",
        ingestion_system_email=os.getenv("RIFTHUB_INGESTION_SYSTEM_EMAIL", "ingestion-bot@localhost").strip()
        or "ingestion-bot@localhost",
    )
