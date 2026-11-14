from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.sqlalchemy_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def tune_sqlite(dbapi_connection: Any, _record: Any = None) -> None:
    """SQLite lets one connection write at a time. Two settings make that painless."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # readers keep reading while somebody writes
    cursor.execute("PRAGMA busy_timeout=30000")  # the next writer waits its turn (default: 5 s)
    cursor.close()


if engine.dialect.name == "sqlite":
    event.listen(engine.sync_engine, "connect", tune_sqlite)


async def create_db_and_tables() -> None:
    from app import models  # noqa: F401  (importing the models registers the tables)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
