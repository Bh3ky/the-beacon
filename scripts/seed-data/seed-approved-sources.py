from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from rifthub_backend import dispose_engine
from rifthub_backend.db.session import get_session_factory
from rifthub_backend.ingestion_sources import import_approved_sources, load_approved_sources

DEFAULT_SOURCE_FILE = Path(__file__).with_name("approved_sources.dev.json")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import approved RiftHub ingestion sources.")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SOURCE_FILE,
        help="Path to the approved sources JSON file.",
    )
    args = parser.parse_args()

    source_inputs = load_approved_sources(args.file)
    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await import_approved_sources(db=db, source_inputs=source_inputs)
    await dispose_engine()
    print(
        f"Imported approved sources from {args.file}: "
        f"inserted={result.inserted_count} updated={result.updated_count}"
    )


if __name__ == "__main__":
    asyncio.run(main())
