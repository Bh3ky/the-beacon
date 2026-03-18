from rifthub_backend.auth.delivery import (
    LoggingVerificationDelivery,
    NoopVerificationDelivery,
    ResendVerificationDelivery,
    build_verification_url,
    get_verification_delivery,
)
from rifthub_backend.config import ConfigError, Settings


def make_settings(**overrides: object) -> Settings:
    base = Settings(
        environment="development",
        log_level="INFO",
        api_host="127.0.0.1",
        api_port=8000,
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        sql_echo=False,
        app_secret="test-secret",
        frontend_base_url="http://localhost:3000",
        verification_delivery_mode="log",
    )
    return base.__class__(**{**base.__dict__, **overrides})


def test_build_verification_url_uses_frontend_base_url() -> None:
    settings = make_settings(frontend_base_url="https://app.example.com")

    url = build_verification_url(settings=settings, token="opaque token")

    assert url == "https://app.example.com/verify?token=opaque+token"


def test_get_verification_delivery_returns_noop_for_noop_mode() -> None:
    delivery = get_verification_delivery(make_settings(environment="test", verification_delivery_mode="noop"))

    assert isinstance(delivery, NoopVerificationDelivery)


def test_get_verification_delivery_returns_logging_adapter_in_development() -> None:
    delivery = get_verification_delivery(make_settings())

    assert isinstance(delivery, LoggingVerificationDelivery)


def test_get_verification_delivery_returns_resend_adapter_when_configured() -> None:
    delivery = get_verification_delivery(
        make_settings(
            environment="production",
            verification_delivery_mode="resend",
            resend_api_key="re_test_key",
            verification_from_email="RiftHub <no-reply@example.com>",
        )
    )

    assert isinstance(delivery, ResendVerificationDelivery)


def test_get_verification_delivery_requires_api_key_for_resend_mode() -> None:
    settings = make_settings(environment="production", verification_delivery_mode="resend")

    try:
        get_verification_delivery(settings)
    except ConfigError as exc:
        assert "RIFTHUB_RESEND_API_KEY" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("Expected resend delivery mode to require an API key.")


def test_get_verification_delivery_rejects_log_mode_outside_dev_and_test() -> None:
    settings = make_settings(environment="production", verification_delivery_mode="log")

    try:
        get_verification_delivery(settings)
    except ConfigError as exc:
        assert "only allowed in development or test" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("Expected log delivery mode to be rejected outside development/test.")
