import logging
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

ORDERS = "/api/v1/orders"
MakePizza = Callable[..., dict[str, Any]]


def order_body(pizza_id: int, **overrides: Any) -> dict[str, Any]:
    return {"pizza_id": pizza_id, "customer_name": "Ayşe", "quantity": 2} | overrides


def test_order_gets_a_total_and_a_message(client: TestClient, make_pizza: MakePizza) -> None:
    pizza = make_pizza(name="Margherita", price=190)
    response = client.post(ORDERS, json=order_body(pizza["id"]))
    assert response.status_code == 201
    order = response.json()
    assert order["total_price"] == 380
    assert order["status"] == "preparing"
    assert order["pizza_name"] == "Margherita"
    assert "Ayşe" in order["message"]
    assert "2 × Margherita" in order["message"]


def test_order_for_an_unknown_pizza_is_404(client: TestClient) -> None:
    response = client.post(ORDERS, json=order_body(999))
    assert response.status_code == 404
    assert response.json()["code"] == "PIZZA_NOT_FOUND"


@pytest.mark.parametrize("quantity", [0, 11])
def test_quantity_is_between_1_and_10(
    client: TestClient, make_pizza: MakePizza, quantity: int
) -> None:
    pizza = make_pizza()
    response = client.post(ORDERS, json=order_body(pizza["id"], quantity=quantity))
    assert response.status_code == 422


def test_quantity_defaults_to_one(client: TestClient, make_pizza: MakePizza) -> None:
    pizza = make_pizza(price=190)
    order = client.post(ORDERS, json={"pizza_id": pizza["id"], "customer_name": "Can"}).json()
    assert order["quantity"] == 1
    assert order["total_price"] == 190


def test_get_and_list_orders(client: TestClient, make_pizza: MakePizza) -> None:
    pizza = make_pizza()
    first = client.post(ORDERS, json=order_body(pizza["id"])).json()
    client.post(ORDERS, json=order_body(pizza["id"], customer_name="Can"))

    assert client.get(f"{ORDERS}/{first['id']}").json() == first
    names = [order["customer_name"] for order in client.get(ORDERS).json()]
    assert names == ["Ayşe", "Can"]
    assert len(client.get(f"{ORDERS}?limit=1").json()) == 1
    assert client.get(f"{ORDERS}/999").status_code == 404


def test_kitchen_is_notified_in_the_background(
    client: TestClient, make_pizza: MakePizza, caplog: pytest.LogCaptureFixture
) -> None:
    pizza = make_pizza()
    with caplog.at_level(logging.INFO, logger="app.services.order"):
        order = client.post(ORDERS, json=order_body(pizza["id"])).json()
    assert f"order #{order['id']}" in caplog.text


def test_chef_moves_an_order_along(
    client: TestClient, chef: dict[str, str], make_pizza: MakePizza
) -> None:
    pizza = make_pizza()
    order = client.post(ORDERS, json=order_body(pizza["id"])).json()
    url = f"{ORDERS}/{order['id']}"

    assert client.patch(url, json={"status": "baking"}).status_code == 401
    response = client.patch(url, json={"status": "baking"}, headers=chef)
    assert response.status_code == 200
    assert response.json()["status"] == "baking"
    assert "oven" in response.json()["message"]
    assert client.patch(url, json={"status": "burnt"}, headers=chef).status_code == 422
    unknown = client.patch(f"{ORDERS}/999", json={"status": "baking"}, headers=chef)
    assert unknown.status_code == 404


def test_a_pizza_with_orders_cannot_be_deleted(
    client: TestClient, chef: dict[str, str], make_pizza: MakePizza
) -> None:
    pizza = make_pizza()
    client.post(ORDERS, json=order_body(pizza["id"]))
    response = client.delete(f"/api/v1/pizzas/{pizza['id']}", headers=chef)
    assert response.status_code == 409
    assert response.json()["code"] == "PIZZA_IN_USE"
