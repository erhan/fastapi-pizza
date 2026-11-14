"""The migrations are written by hand, so make sure they build exactly what the models describe."""

from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.core.config import settings
from app.core.db import Base

ROOT = Path(__file__).parent.parent


def test_migrations_match_the_models(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database = tmp_path / "migrated.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite+aiosqlite:///{database}")
    config = Config(ROOT / "alembic.ini")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database}")
    with engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert differences == []  # nothing left for `alembic revision --autogenerate` to add

    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
