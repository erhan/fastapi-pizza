"""The talk's building blocks must really work: every example is exercised here."""

import asyncio
import importlib.util
import time
from pathlib import Path
from types import ModuleType

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

EXAMPLES = Path(__file__).parent.parent / "examples"
DELAY = 0.3  # seconds a pizza "bakes" in the async examples


def load(name: str) -> ModuleType:
    """Example files start with a digit, so they can't be imported by name."""
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_01_hello() -> None:
    client = TestClient(load("01_hello").app)
    assert client.get("/").json() == {"message": "Merhaba Python Pizza! 🍕"}


def test_02_four_cheeses_path_query_body_header() -> None:
    client = TestClient(load("02_params").app)
    response = client.post(
        "/pizzas/3/orders",
        params={"extra_cheese": "true"},
        headers={"X-Table-No": "7"},
        json={"customer": "Ayşe", "quantity": 2},
    )
    assert response.json() == {
        "pizza_id": 3,
        "extra_cheese": True,
        "table": 7,
        "order": {"customer": "Ayşe", "quantity": 2},
    }
    assert client.post("/pizzas/margherita/orders", json={"customer": "x"}).status_code == 422


def test_03_models_pineapple_gets_a_422() -> None:
    client = TestClient(load("03_models").app)
    margherita = {"name": "Margherita", "price": 190, "toppings": ["mozzarella", "basil"]}
    assert client.post("/pizzas", json=margherita).status_code == 201

    hawaii = {"name": "Hawaii", "price": 200, "toppings": ["mozzarella", "ananas"]}
    response = client.post("/pizzas", json=hawaii)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "toppings", 1]


def test_04_depends() -> None:
    client = TestClient(load("04_depends").app)
    assert client.get("/menu").json()["page"] == {"limit": 10, "offset": 0}
    assert client.get("/menu?limit=2&offset=4").json()["page"] == {"limit": 2, "offset": 4}
    assert client.delete("/menu/Pepperoni").status_code == 401
    chef = client.delete("/menu/Pepperoni", headers={"X-API-Key": "chef-secret"})
    assert chef.json() == {"removed": "Pepperoni"}


@pytest.fixture
def bakery() -> FastAPI:
    module = load("05_async")
    module.BAKE_SECONDS = DELAY
    return module.app


async def three_orders_at_once(app: FastAPI, path: str) -> float:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://bakery") as client:
        started = time.perf_counter()
        responses = await asyncio.gather(*(client.get(path) for _ in range(3)))
        elapsed = time.perf_counter() - started
    assert [response.status_code for response in responses] == [200, 200, 200]
    return elapsed


def test_05_one_async_waiter_serves_all_tables_at_once(bakery: FastAPI) -> None:
    elapsed = asyncio.run(three_orders_at_once(bakery, "/bake/async"))
    assert elapsed < 2 * DELAY  # three pizzas baked side by side


def test_05_a_blocking_call_freezes_the_whole_restaurant(bakery: FastAPI) -> None:
    elapsed = asyncio.run(three_orders_at_once(bakery, "/bake/blocking"))
    assert elapsed > 2.5 * DELAY  # one pizza after another


def test_05_def_endpoints_run_in_the_threadpool(bakery: FastAPI) -> None:
    elapsed = asyncio.run(three_orders_at_once(bakery, "/bake/threadpool"))
    assert elapsed < 2 * DELAY
