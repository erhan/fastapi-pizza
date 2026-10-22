from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.services import pizza as pizza_service

URL = "/api/v1/pizzas"
MakePizza = Callable[..., dict[str, Any]]


def test_menu_starts_empty(client: TestClient) -> None:
    assert client.get(URL).json() == []


def test_filters(client: TestClient, make_pizza: MakePizza) -> None:
    make_pizza(name="Margherita", price=190)
    make_pizza(name="Pepperoni", price=230, toppings=["mozzarella", "pepperoni"])
    make_pizza(name="Sucuklu", price=240, toppings=["mozzarella", "sucuk"])

    def names(query: str) -> list[str]:
        return [pizza["name"] for pizza in client.get(f"{URL}?{query}").json()]

    assert names("vegetarian=true") == ["Margherita"]
    assert names("vegetarian=false") == ["Pepperoni", "Sucuklu"]
    assert names("max_price=200") == ["Margherita"]
    assert names("vegetarian=false&max_price=235") == ["Pepperoni"]


def test_pagination(client: TestClient, make_pizza: MakePizza) -> None:
    for number in range(3):
        make_pizza(name=f"Pizza {number}")

    first_two = client.get(f"{URL}?limit=2").json()
    assert [pizza["name"] for pizza in first_two] == ["Pizza 0", "Pizza 1"]
    rest = client.get(f"{URL}?limit=2&offset=2").json()
    assert [pizza["name"] for pizza in rest] == ["Pizza 2"]


@pytest.mark.parametrize("query", ["limit=0", "limit=51", "offset=-1", "max_price=0"])
def test_bad_query_params_are_rejected(client: TestClient, query: str) -> None:
    assert client.get(f"{URL}?{query}").status_code == 422


def test_get_pizza(client: TestClient, make_pizza: MakePizza) -> None:
    created = make_pizza()
    response = client.get(f"{URL}/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_unknown_pizza_is_404(client: TestClient) -> None:
    response = client.get(f"{URL}/999")
    assert response.status_code == 404
    assert response.json()["code"] == "PIZZA_NOT_FOUND"


def test_pizza_id_must_be_an_int(client: TestClient) -> None:
    response = client.get(f"{URL}/margherita")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "pizza_id"]


def test_create_pizza(client: TestClient, chef: dict[str, str]) -> None:
    body = {"name": "Vejetaryen", "price": 220, "size": "large", "toppings": ["mushroom", "olive"]}
    response = client.post(URL, json=body, headers=chef)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == 1
    assert created["size"] == "large"
    assert created["is_vegetarian"] is True


def test_pineapple_is_rejected(client: TestClient, chef: dict[str, str]) -> None:
    body = {"name": "Hawaii", "price": 200, "toppings": ["mozzarella", "ananas"]}
    response = client.post(URL, json=body, headers=chef)
    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "toppings", 1]
    assert error["input"] == "ananas"
    assert client.get(URL).json() == []  # nothing was created


@pytest.mark.parametrize(
    "body",
    [
        {"name": "X", "price": 190, "toppings": ["basil"]},  # name is too short
        {"name": "Free", "price": 0, "toppings": ["basil"]},  # price must be > 0
        {"name": "Bare", "price": 190, "toppings": []},  # at least one topping
    ],
)
def test_invalid_bodies_are_rejected(
    client: TestClient, chef: dict[str, str], body: dict[str, Any]
) -> None:
    assert client.post(URL, json=body, headers=chef).status_code == 422


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-API-Key": "wrong"}, {"X-API-Key": "şef".encode()}],
    ids=["no key", "wrong key", "non-ascii key"],
)
def test_writes_need_the_chef_key(
    client: TestClient, make_pizza: MakePizza, headers: dict[str, Any]
) -> None:
    url = f"{URL}/{make_pizza()['id']}"
    body = {"name": "Nope", "price": 100, "toppings": ["basil"]}
    assert client.post(URL, json=body, headers=headers).status_code == 401
    assert client.patch(url, json={"price": 1}, headers=headers).status_code == 401
    assert client.delete(url, headers=headers).status_code == 401


def test_patch_changes_only_what_was_sent(
    client: TestClient, chef: dict[str, str], make_pizza: MakePizza
) -> None:
    pizza = make_pizza(price=190)
    response = client.patch(f"{URL}/{pizza['id']}", json={"price": 205}, headers=chef)
    assert response.status_code == 200
    assert response.json() == pizza | {"price": 205}


def test_patch_recomputes_is_vegetarian(
    client: TestClient, chef: dict[str, str], make_pizza: MakePizza
) -> None:
    pizza = make_pizza()
    assert pizza["is_vegetarian"] is True
    body = {"toppings": ["mozzarella", "sucuk"]}
    response = client.patch(f"{URL}/{pizza['id']}", json=body, headers=chef)
    assert response.json()["is_vegetarian"] is False


def test_patch_with_null_changes_nothing(
    client: TestClient, chef: dict[str, str], make_pizza: MakePizza
) -> None:
    pizza = make_pizza()
    response = client.patch(f"{URL}/{pizza['id']}", json={"name": None}, headers=chef)
    assert response.status_code == 200
    assert response.json() == pizza


def test_patch_unknown_pizza_is_404(client: TestClient, chef: dict[str, str]) -> None:
    assert client.patch(f"{URL}/999", json={"price": 1}, headers=chef).status_code == 404


def test_delete_pizza(client: TestClient, chef: dict[str, str], make_pizza: MakePizza) -> None:
    url = f"{URL}/{make_pizza()['id']}"
    assert client.delete(url, headers=chef).status_code == 204
    assert client.get(url).status_code == 404


def test_delete_unknown_pizza_is_404(client: TestClient, chef: dict[str, str]) -> None:
    assert client.delete(f"{URL}/999", headers=chef).status_code == 404


def test_seed_fills_an_empty_menu_exactly_once(client: TestClient, engine: AsyncEngine) -> None:
    async def seed_twice() -> None:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            await pizza_service.seed_menu(db)
            await pizza_service.seed_menu(db)

    client.portal.call(seed_twice)
    menu = client.get(f"{URL}?limit=50").json()
    assert len(menu) == len(pizza_service.MENU)
    assert any(pizza["is_vegetarian"] for pizza in menu)
    assert any(not pizza["is_vegetarian"] for pizza in menu)
