from __future__ import annotations

from types import SimpleNamespace

import pytest

from rifthub_backend.db.types import UserRole
from rifthub_backend.user_roles import RoleAssignmentError, assign_user_role


@pytest.mark.anyio
async def test_assign_user_role_updates_existing_user() -> None:
    user = SimpleNamespace(email="ops@example.com", role=UserRole.USER)

    class FakeDbSession:
        def __init__(self) -> None:
            self.committed = False
            self.refreshed = False

        async def scalar(self, _statement: object):
            return user

        async def commit(self) -> None:
            self.committed = True

        async def refresh(self, refreshed_user: object) -> None:
            assert refreshed_user is user
            self.refreshed = True

    db = FakeDbSession()
    updated = await assign_user_role(
        db=db,  # type: ignore[arg-type]
        email=" Ops@Example.com ",
        role=UserRole.ADMIN,
    )

    assert updated is user
    assert user.role == UserRole.ADMIN
    assert db.committed is True
    assert db.refreshed is True


@pytest.mark.anyio
async def test_assign_user_role_raises_for_missing_user() -> None:
    class FakeDbSession:
        async def scalar(self, _statement: object):
            return None

    with pytest.raises(RoleAssignmentError, match="does not exist"):
        await assign_user_role(
            db=FakeDbSession(),  # type: ignore[arg-type]
            email="missing@example.com",
            role=UserRole.MODERATOR,
        )
