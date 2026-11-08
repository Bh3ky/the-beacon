from types import SimpleNamespace
from uuid import uuid4

import pytest
from rifthub_api.dependencies import limit_per_user
from rifthub_api.errors import ApiError


def _session(user_id=None):
    # The guard only reads current_session.user.id, so a stand-in is enough.
    return SimpleNamespace(user=SimpleNamespace(id=user_id or uuid4()))


def _guard(limit: int):
    # A unique action name per test, so counters from other tests can't leak in.
    return limit_per_user(f"test-{uuid4()}", limit=limit, window_seconds=60, message="slow down")


@pytest.mark.anyio
async def test_user_within_limit_is_allowed() -> None:
    guard, session = _guard(2), _session()
    await guard(session)
    await guard(session)


@pytest.mark.anyio
async def test_user_over_limit_gets_429() -> None:
    guard, session = _guard(2), _session()
    await guard(session)
    await guard(session)
    with pytest.raises(ApiError) as exc_info:
        await guard(session)
    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "rate_limited"


@pytest.mark.anyio
async def test_one_users_limit_does_not_affect_another_user() -> None:
    guard = _guard(1)
    await guard(_session())
    await guard(_session())  # different user, so it is allowed
