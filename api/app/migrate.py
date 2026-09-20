import asyncio
from pathlib import Path

from alembic.config import Config
from sqlalchemy import inspect

from alembic import command
from app.db import engine

BASELINE_REVISION = "20260917_0001"


async def existing_tables() -> set[str]:
    async with engine.connect() as connection:
        tables = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).get_table_names()
        )
    await engine.dispose()
    return set(tables)


def alembic_config() -> Config:
    root = Path(__file__).resolve().parents[1]
    return Config(str(root / "alembic.ini"))


def migrate() -> None:
    tables = asyncio.run(existing_tables())
    config = alembic_config()
    if "quote_requests" in tables and "alembic_version" not in tables:
        command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")


if __name__ == "__main__":
    migrate()
