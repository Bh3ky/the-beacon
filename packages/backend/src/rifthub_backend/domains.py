from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.models.domain import Domain


async def resolve_or_create_domain(*, db: AsyncSession, hostname: str) -> Domain:
    insert_stmt = (
        pg_insert(Domain)
        .values(hostname=hostname)
        .on_conflict_do_nothing(index_elements=["hostname"])
    )
    await db.execute(insert_stmt)
    domain = await db.scalar(select(Domain).where(Domain.hostname == hostname))
    if domain is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Failed to resolve domain.")
    return domain
