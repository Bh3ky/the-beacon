from __future__ import annotations

from rifthub_backend.db.types import UserStatus


WRITE_RESTRICTED_STATUSES = frozenset({UserStatus.SUSPENDED, UserStatus.BANNED})


def user_has_restricted_write_access(*, status: UserStatus) -> bool:
    return status in WRITE_RESTRICTED_STATUSES
