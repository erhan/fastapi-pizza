from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture
def engine() -> AsyncEngine:
    """A brand-new in-memory SQLite database for every test."""
    return create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)


@pytest.fixture
def client(engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # The app's own startup would touch the real pizza.db, so switch that off in tests.
    monkeypatch.setattr(settings, "create_tables_on_startup", False)
    monkeypatch.setattr(settings, "seed_on_startup", False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.portal.call(create_tables)
        yield test_client
        test_client.portal.call(engine.dispose)
    app.dependency_overrides.clear()


@pytest.fixture
def chef() -> dict[str, str]:
    """The headers of the one person who may change the menu."""
    return {"X-API-Key": settings.api_key}


@pytest.fixture
def make_pizza(client: TestClient, chef: dict[str, str]) -> Callable[..., dict[str, Any]]:
    """Add a pizza through the API. Override any field: make_pizza(price=250)."""

    def _make(**overrides: Any) -> dict[str, Any]:
        body = {"name": "Margherita", "price": 190, "toppings": ["mozzarella", "tomato", "basil"]}
        response = client.post("/api/v1/pizzas", json=body | overrides, headers=chef)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
