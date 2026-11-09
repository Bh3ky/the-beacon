import pytest
import rifthub_backend.config as config_module
from rifthub_backend.config import ConfigError, get_settings


def test_settings_require_database_url(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setattr(config_module, "_load_dotenv", lambda: None)
    monkeypatch.delenv("RIFTHUB_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_ENV", raising=False)
    monkeypatch.delenv("RIFTHUB_LOG_LEVEL", raising=False)
    monkeypatch.delenv("RIFTHUB_API_HOST", raising=False)
    monkeypatch.delenv("RIFTHUB_API_PORT", raising=False)
    monkeypatch.delenv("RIFTHUB_SQL_ECHO", raising=False)

    with pytest.raises(ConfigError, match="RIFTHUB_DATABASE_URL"):
        get_settings()


def test_settings_honor_database_overrides(monkeypatch) -> None:
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setattr(config_module, "_load_dotenv", lambda: None)
    monkeypatch.setenv(
        "RIFTHUB_DATABASE_URL",
        "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )
    monkeypatch.setenv(
        "RIFTHUB_MIGRATION_DATABASE_URL",
        "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_migration",
    )
    monkeypatch.setenv("RIFTHUB_SQL_ECHO", "true")

    settings = get_settings()

    assert settings.database_url.endswith("/rifthub_test")
    assert settings.migration_database_url.endswith("/rifthub_migration")
    assert settings.sql_echo is True


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
    ],
)
def test_settings_parse_sql_echo_boolean_values(
    monkeypatch,
    raw_value: str,
    expected: bool,
) -> None:
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setattr(config_module, "_load_dotenv", lambda: None)
    monkeypatch.setenv(
        "RIFTHUB_DATABASE_URL",
        "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )
    monkeypatch.delenv("RIFTHUB_MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_ENV", raising=False)
    monkeypatch.delenv("RIFTHUB_LOG_LEVEL", raising=False)
    monkeypatch.delenv("RIFTHUB_API_HOST", raising=False)
    monkeypatch.delenv("RIFTHUB_API_PORT", raising=False)
    monkeypatch.setenv("RIFTHUB_SQL_ECHO", raw_value)

    settings = get_settings()

    assert settings.sql_echo is expected


def test_settings_default_migration_url_from_primary(monkeypatch) -> None:
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setattr(config_module, "_load_dotenv", lambda: None)
    monkeypatch.setenv(
        "RIFTHUB_DATABASE_URL",
        "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )
    monkeypatch.delenv("RIFTHUB_MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_ENV", raising=False)
    monkeypatch.delenv("RIFTHUB_LOG_LEVEL", raising=False)
    monkeypatch.delenv("RIFTHUB_API_HOST", raising=False)
    monkeypatch.delenv("RIFTHUB_API_PORT", raising=False)
    monkeypatch.delenv("RIFTHUB_SQL_ECHO", raising=False)

    settings = get_settings()

    assert settings.database_url.endswith("/rifthub_test")
    assert settings.migration_database_url == settings.database_url
    assert settings.sql_echo is False


def test_settings_apply_default_non_database_values(monkeypatch) -> None:
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setattr(config_module, "_load_dotenv", lambda: None)
    monkeypatch.setenv(
        "RIFTHUB_DATABASE_URL",
        "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )
    monkeypatch.delenv("RIFTHUB_MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_ENV", raising=False)
    monkeypatch.delenv("RIFTHUB_LOG_LEVEL", raising=False)
    monkeypatch.delenv("RIFTHUB_API_HOST", raising=False)
    monkeypatch.delenv("RIFTHUB_API_PORT", raising=False)
    monkeypatch.delenv("RIFTHUB_SQL_ECHO", raising=False)

    settings = get_settings()

    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.app_secret == "dev-insecure-secret"
    assert settings.session_cookie_name == "rifthub_session"
    assert settings.csrf_cookie_name == "rifthub_csrf"
    assert settings.session_idle_minutes == 30
    assert settings.session_absolute_hours == 24
    assert settings.session_touch_interval_minutes == 10
    assert settings.verification_token_ttl_hours == 24
    assert settings.verification_delivery_mode == "log"
    assert settings.frontend_base_url == "http://localhost:3000"
    assert settings.verification_from_email == "noreply@localhost"
    assert settings.verification_smtp_host == "127.0.0.1"
    assert settings.verification_smtp_port == 1025
    assert settings.verification_smtp_starttls is False
    assert settings.resend_api_key == ""
    assert settings.allowed_origins == ("http://localhost:3000", "http://127.0.0.1:3000")
    assert settings.rate_limit_backend == "memory"
    assert settings.redis_url == ""
    assert settings.rate_limit_prefix == "rifthub:rate-limit"
    assert settings.proxy_secret == ""


def test_settings_require_redis_url_when_redis_rate_limiter_is_enabled(monkeypatch) -> None:
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setattr(config_module, "_load_dotenv", lambda: None)
    monkeypatch.setenv(
        "RIFTHUB_DATABASE_URL",
        "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )
    monkeypatch.setenv("RIFTHUB_ENV", "production")
    monkeypatch.setenv("RIFTHUB_PROXY_SECRET", "x")
    monkeypatch.delenv("RIFTHUB_REDIS_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_RATE_LIMIT_BACKEND", raising=False)

    with pytest.raises(ConfigError, match="RIFTHUB_REDIS_URL"):
        get_settings()


def test_settings_load_repo_root_dotenv(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", False)
    monkeypatch.delenv("RIFTHUB_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIFTHUB_ENV", raising=False)
    monkeypatch.delenv("RIFTHUB_LOG_LEVEL", raising=False)
    monkeypatch.delenv("RIFTHUB_API_HOST", raising=False)
    monkeypatch.delenv("RIFTHUB_API_PORT", raising=False)
    monkeypatch.delenv("RIFTHUB_SQL_ECHO", raising=False)

    (tmp_path / ".env").write_text(
        "\n".join(  # noqa: FLY002 - a list is easier to read than one long f-string
            [
                "RIFTHUB_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/from_dotenv",
                "RIFTHUB_MIGRATION_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/from_dotenv_migration",
                "RIFTHUB_SQL_ECHO=true",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()

    assert settings.database_url.endswith("/from_dotenv")
    assert settings.migration_database_url.endswith("/from_dotenv_migration")
    assert settings.sql_echo is True


VALID_PRODUCTION_ENV = {
    "RIFTHUB_DATABASE_URL": "postgresql+asyncpg://user:pass@db.example.com:5432/rifthub",
    "RIFTHUB_ENV": "production",
    "RIFTHUB_REDIS_URL": "redis://redis.example.com:6379/0",
    "RIFTHUB_APP_SECRET": "a" * 32,
    "RIFTHUB_PROXY_SECRET": "b" * 32,
    "RIFTHUB_FRONTEND_BASE_URL": "https://rifthub.example.com",
    "RIFTHUB_ALLOWED_ORIGINS": "https://rifthub.example.com",
    "RIFTHUB_VERIFICATION_DELIVERY_MODE": "resend",
    "RIFTHUB_RESEND_API_KEY": "re_test_key",
    "RIFTHUB_VERIFICATION_FROM_EMAIL": "RiftHub <noreply@rifthub.example.com>",
}


def _use_production_env(monkeypatch, **overrides) -> None:
    # Don't read the real .env file; use only the values listed here.
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setattr(config_module, "_load_dotenv", lambda: None)
    monkeypatch.delenv("RIFTHUB_RATE_LIMIT_BACKEND", raising=False)
    for name, value in {**VALID_PRODUCTION_ENV, **overrides}.items():
        monkeypatch.setenv(name, value)


def test_valid_production_settings_are_accepted(monkeypatch) -> None:
    _use_production_env(monkeypatch)
    assert get_settings().environment == "production"


@pytest.mark.parametrize(
    ("name", "bad_value"),
    [
        ("RIFTHUB_APP_SECRET", "too-short"),
        ("RIFTHUB_PROXY_SECRET", "too-short"),
        ("RIFTHUB_FRONTEND_BASE_URL", "http://localhost:3000"),
        ("RIFTHUB_ALLOWED_ORIGINS", "http://localhost:3000"),
        ("RIFTHUB_VERIFICATION_DELIVERY_MODE", "noop"),
        ("RIFTHUB_RESEND_API_KEY", ""),
        ("RIFTHUB_VERIFICATION_FROM_EMAIL", "noreply@localhost"),
    ],
)
def test_unsafe_production_settings_are_rejected(monkeypatch, name, bad_value) -> None:
    _use_production_env(monkeypatch, **{name: bad_value})
    with pytest.raises(ConfigError, match=name):
        get_settings()
