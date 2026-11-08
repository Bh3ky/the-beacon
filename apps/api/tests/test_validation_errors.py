import pytest
import rifthub_api.main as main_module
from fastapi.testclient import TestClient
from pydantic import ValidationError
from rifthub_api.routes.flags import CreateFlagRequest
from rifthub_api.routes.posts import CreateCommentRequest, CreatePostRequest
from rifthub_backend.config import Settings


def test_non_json_body_returns_422_not_500(monkeypatch) -> None:
    # Same setup as test_health.py: fake settings and fake DB startup/shutdown,
    # so this test never needs a real database.
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )

    async def fake_ping_database(engine: object | None = None) -> None:
        pass

    async def fake_dispose_engine() -> None:
        pass

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(main_module, "get_engine", lambda: object())
    monkeypatch.setattr(main_module, "ping_database", fake_ping_database)
    monkeypatch.setattr(main_module, "dispose_engine", fake_dispose_engine)

    with TestClient(main_module.create_app()) as client:
        # data=... sends form data, not JSON. This is the request that used to crash.
        response = client.post("/v1/auth/login", data={"x": "1"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def _post(**overrides):
    # A valid post, with any fields you pass in replaced.
    data = {"post_type": "text", "category": "ask", "title": "Hello", "body_markdown": "hi"}
    data.update(overrides)
    return CreatePostRequest(**data)


def test_post_title_of_300_chars_is_accepted() -> None:
    # Exactly at the limit must still work (checks we're not off by one).
    _post(title="a" * 300)


def test_post_title_over_300_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _post(title="a" * 301)


def test_post_empty_title_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _post(title="")


def test_post_body_over_20k_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _post(body_markdown="x" * 20_001)


def test_comment_over_10k_chars_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateCommentRequest(body_markdown="x" * 10_001)


def test_flag_notes_over_1000_chars_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateFlagRequest(
            target_type="post",
            target_id="4fd46e5f-199e-4a5e-8ddf-c1ebce0ec961",
            reason_code="spam",
            notes="x" * 1001,
        )
