from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

import rifthub_backend.creation as creation_module
from rifthub_backend.creation import (
    ACTIVE_LINK_URL_CONSTRAINT_NAME,
    CreatePostInput,
    CreationError,
    _is_active_link_duplicate_error,
    create_post,
    hostname_from_url,
    normalize_url,
    slugify_title,
)
from rifthub_backend.db.types import Category, PostType, UserRole, UserStatus


def test_slugify_title_normalizes_and_truncates() -> None:
    slug = slugify_title("  African startups are rethinking logistics infrastructure!!!  ")

    assert slug == "african-startups-are-rethinking-logistics-infrastructure"


def test_slugify_title_falls_back_when_ascii_slug_is_empty() -> None:
    assert slugify_title("🔥🔥🔥") == "post"


def test_normalize_url_lowercases_scheme_and_host_and_strips_default_port() -> None:
    normalized = normalize_url(" HTTPS://Example.COM:443/Story?q=1#frag ")

    assert normalized == "https://example.com/Story?q=1"
    assert hostname_from_url(normalized) == "example.com"


def test_normalize_url_rejects_non_http_scheme() -> None:
    with pytest.raises(CreationError, match="URL must use http or https"):
        normalize_url("ftp://example.com/file")


def test_duplicate_link_integrity_detection_checks_named_partial_index() -> None:
    duplicate_exc = IntegrityError(
        "insert into posts ...",
        {},
        SimpleNamespace(diag=SimpleNamespace(constraint_name=ACTIVE_LINK_URL_CONSTRAINT_NAME)),
    )
    other_exc = IntegrityError(
        "insert into posts ...",
        {},
        SimpleNamespace(diag=SimpleNamespace(constraint_name="other_constraint")),
    )

    assert _is_active_link_duplicate_error(duplicate_exc) is True
    assert _is_active_link_duplicate_error(other_exc) is False


@pytest.mark.anyio
async def test_create_post_translates_duplicate_link_integrity_error(monkeypatch) -> None:
    author = SimpleNamespace(
        id=uuid4(),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    existing_post = SimpleNamespace(id=uuid4(), slug="existing-post")
    duplicate_exc = IntegrityError(
        "insert into posts ...",
        {},
        SimpleNamespace(diag=SimpleNamespace(constraint_name=ACTIVE_LINK_URL_CONSTRAINT_NAME)),
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.scalar_calls = 0

        async def scalar(self, _query: object) -> object | None:
            self.scalar_calls += 1
            if self.scalar_calls == 1:
                return None
            return existing_post

        def add(self, _obj: object) -> None:
            return None

        async def flush(self) -> None:
            raise duplicate_exc

        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            return None

    async def fake_resolve_or_create_domain(**_: object) -> object:
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr(creation_module, "resolve_or_create_domain", fake_resolve_or_create_domain)

    with pytest.raises(CreationError) as exc_info:
        await create_post(
            db=FakeDbSession(),  # type: ignore[arg-type]
            author=author,  # type: ignore[arg-type]
            payload=CreatePostInput(
                post_type=PostType.LINK,
                category=Category.ECOSYSTEM,
                title="Duplicate link",
                url="https://example.com/story#comments",
                body_markdown=None,
                job_expires_at=None,
            ),
        )

    exc = exc_info.value
    assert exc.status_code == 409
    assert exc.code == "duplicate_submission"
    assert exc.details == {
        "existing_post_id": str(existing_post.id),
        "existing_post_slug": "existing-post",
    }
