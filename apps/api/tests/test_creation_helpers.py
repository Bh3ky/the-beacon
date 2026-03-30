from datetime import UTC, datetime, timedelta
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
from rifthub_backend.voting import compute_post_rank_score


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
        return SimpleNamespace(id=uuid4(), trust_score=1.0)

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


@pytest.mark.anyio
async def test_create_post_sets_initial_rank_score(monkeypatch) -> None:
    author = SimpleNamespace(
        id=uuid4(),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.added_post = None

        async def scalar(self, _query: object) -> object | None:
            return None

        def add(self, obj: object) -> None:
            self.added_post = obj

        async def flush(self) -> None:
            return None

        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            return None

    db = FakeDbSession()

    async def fake_get_post_detail(**_: object):
        return db.added_post

    monkeypatch.setattr(creation_module, "get_post_detail", fake_get_post_detail)

    post = await create_post(
        db=db,  # type: ignore[arg-type]
        author=author,  # type: ignore[arg-type]
        payload=CreatePostInput(
            post_type=PostType.TEXT,
            category=Category.ASK,
            title="Founders are sharing better launch notes",
            url=None,
            body_markdown="Body",
            job_expires_at=None,
        ),
    )

    assert post is db.added_post
    assert db.added_post.rank_score > 0
    assert db.added_post.rank_score == compute_post_rank_score(
        score=0,
        submitted_at=db.added_post.submitted_at,
        comment_count=0,
        category=Category.ASK,
        now=db.added_post.submitted_at,
    )
    assert db.added_post.job_expires_at is None


@pytest.mark.anyio
async def test_create_job_post_defaults_to_thirty_day_expiry(monkeypatch) -> None:
    author = SimpleNamespace(
        id=uuid4(),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.added_post = None

        async def scalar(self, _query: object) -> object | None:
            return None

        def add(self, obj: object) -> None:
            self.added_post = obj

        async def flush(self) -> None:
            return None

        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            return None

    db = FakeDbSession()

    async def fake_get_post_detail(**_: object):
        return db.added_post

    monkeypatch.setattr(creation_module, "get_post_detail", fake_get_post_detail)

    await create_post(
        db=db,  # type: ignore[arg-type]
        author=author,  # type: ignore[arg-type]
        payload=CreatePostInput(
            post_type=PostType.JOB,
            category=Category.JOBS,
            title="Senior Backend Engineer",
            url=None,
            body_markdown="Remote-friendly role",
            job_expires_at=None,
        ),
    )

    assert db.added_post.job_expires_at is not None
    assert db.added_post.job_expires_at == db.added_post.submitted_at + timedelta(days=30)


@pytest.mark.anyio
async def test_create_post_rejects_non_job_expiry(monkeypatch) -> None:
    author = SimpleNamespace(
        id=uuid4(),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )

    class FakeDbSession:
        async def scalar(self, _query: object) -> object | None:
            return None

        def add(self, _obj: object) -> None:
            return None

        async def flush(self) -> None:
            return None

        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            return None

    with pytest.raises(CreationError, match="only allowed for job posts"):
        await create_post(
            db=FakeDbSession(),  # type: ignore[arg-type]
            author=author,  # type: ignore[arg-type]
            payload=CreatePostInput(
                post_type=PostType.TEXT,
                category=Category.ASK,
                title="A text post",
                url=None,
                body_markdown="Body",
                job_expires_at=datetime.now(UTC) + timedelta(days=1),
            ),
        )


@pytest.mark.anyio
async def test_create_comment_sets_initial_comment_rank_score_and_refreshes_post_rank(monkeypatch) -> None:
    author = SimpleNamespace(
        id=uuid4(),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    post = SimpleNamespace(
        id=uuid4(),
        status="active",
        comment_count=3,
        score=9,
        submitted_at=datetime.now(UTC),
        category=Category.ECOSYSTEM,
        domain=None,
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.added_comment = None
            self.executed_statement = None

        async def scalar(self, _query: object) -> object | None:
            return post

        def add(self, obj: object) -> None:
            self.added_comment = obj

        async def flush(self) -> None:
            return None

        async def execute(self, statement: object) -> None:
            self.executed_statement = statement

        async def commit(self) -> None:
            return None

    db = FakeDbSession()

    async def fake_get_comment_detail(**_: object):
        return db.added_comment

    monkeypatch.setattr(creation_module, "get_comment_detail", fake_get_comment_detail)

    comment = await creation_module.create_comment(
        db=db,  # type: ignore[arg-type]
        author=author,  # type: ignore[arg-type]
        post_id=post.id,
        payload=creation_module.CreateCommentInput(
            body_markdown="Interesting shift in distribution economics.",
            parent_comment_id=None,
        ),
    )

    assert comment is db.added_comment
    assert db.added_comment.rank_score > 0

    updated_values = {
        column.key: value
        for column, value in db.executed_statement._values.items()  # type: ignore[union-attr]
    }
    assert "rank_score" in updated_values
    assert "last_commented_at" in updated_values
