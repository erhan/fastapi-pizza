"""SQLite lets one connection write at a time. The app sets it up so that the others queue."""

import asyncio
import time
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.db import tune_sqlite


def test_a_second_writer_waits_its_turn(tmp_path: Path) -> None:
    async def two_orders_at_once() -> tuple[list[str], float]:
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'pizza.db'}")
        event.listen(engine.sync_engine, "connect", tune_sqlite)
        async with engine.begin() as conn:
            await conn.execute(text("CREATE TABLE orders (id INTEGER PRIMARY KEY, who TEXT)"))
            assert (await conn.exec_driver_sql("PRAGMA journal_mode")).scalar() == "wal"
            # the default is 5 s: under load that is how you get "database is locked"
            assert (await conn.exec_driver_sql("PRAGMA busy_timeout")).scalar() == 30_000
        session = async_sessionmaker(engine)
        ayse_is_writing = asyncio.Event()

        async def ayse() -> None:
            async with session() as db:
                await db.execute(text("INSERT INTO orders (who) VALUES ('Ayşe')"))
                ayse_is_writing.set()
                await asyncio.sleep(0.3)  # takes her time, still holding the write lock
                await db.commit()

        async def can() -> float:
            await ayse_is_writing.wait()
            started = time.perf_counter()
            async with session() as db:
                await db.execute(text("INSERT INTO orders (who) VALUES ('Can')"))
                await db.commit()
            return time.perf_counter() - started

        _, waited = await asyncio.gather(ayse(), can())
        async with session() as db:
            names = (await db.scalars(text("SELECT who FROM orders ORDER BY id"))).all()
        await engine.dispose()
        return list(names), waited

    names, waited = asyncio.run(two_orders_at_once())
    assert names == ["Ayşe", "Can"]  # nobody got "database is locked"
    assert waited > 0.2  # Can really did wait for Ayşe
