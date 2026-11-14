from collections.abc import Callable
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core import security
from app.core.config import settings

AUTH = "/api/v1/auth"
ME = "/api/v1/users/me"
ORDERS = "/api/v1/orders"
MakePizza = Callable[..., dict[str, Any]]

AYSE = {"email": "ayse@example.com", "password": "margherita-4ever", "full_name": "Ayşe"}


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    """600 000 rounds are for attackers, not for the test suite."""
    monkeypatch.setattr(security, "ITERATIONS", 1_000)


def log_in(client: TestClient, email: str = AYSE["email"], password: str = AYSE["password"]):
    return client.post(f"{AUTH}/token", data={"username": email, "password": password})


@pytest.fixture
def ayse(client: TestClient) -> dict[str, str]:
    """A registered customer, as the headers of a logged-in request."""
    assert client.post(f"{AUTH}/register", json=AYSE).status_code == 201
    return {"Authorization": f"Bearer {log_in(client).json()['access_token']}"}


def test_register_returns_the_user_but_never_the_password(client: TestClient) -> None:
    response = client.post(f"{AUTH}/register", json=AYSE)
    assert response.status_code == 201
    user = response.json()
    assert user["email"] == "ayse@example.com"
    assert user["full_name"] == "Ayşe"
    assert not any("password" in key for key in user)


def test_an_email_can_register_only_once_whatever_its_case(client: TestClient) -> None:
    assert client.post(f"{AUTH}/register", json=AYSE).status_code == 201
    again = client.post(f"{AUTH}/register", json=AYSE | {"email": "AYSE@Example.com"})
    assert again.status_code == 409
    assert again.json()["code"] == "EMAIL_TAKEN"


@pytest.mark.parametrize(
    "change",
    [
        {"email": "not-an-email"},
        {"password": "short"},  # at least 8 characters
        {"full_name": "A"},  # at least 2 characters
    ],
)
def test_invalid_sign_ups_are_rejected(client: TestClient, change: dict[str, str]) -> None:
    assert client.post(f"{AUTH}/register", json=AYSE | change).status_code == 422


def test_passwords_are_stored_hashed() -> None:
    hashed = security.hash_password("margherita-4ever")
    assert "margherita" not in hashed
    assert security.verify_password("margherita-4ever", hashed)
    assert not security.verify_password("hawaii-4ever", hashed)
    assert not security.verify_password("margherita-4ever", "not-a-hash")


def test_the_database_never_waits_for_the_hashing(
    client: TestClient, engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hashing is slow on purpose. A request that kept its database connection meanwhile would,
    with enough sign-ups at once, leave none for the people who only want to see the menu."""
    connections_in_use = 0
    seen: list[int] = []

    def taken(*_: object) -> None:
        nonlocal connections_in_use
        connections_in_use += 1

    def given_back(*_: object) -> None:
        nonlocal connections_in_use
        connections_in_use -= 1

    event.listen(engine.sync_engine, "checkout", taken)
    event.listen(engine.sync_engine, "checkin", given_back)
    hash_password, verify_password = security.hash_password, security.verify_password

    def watched_hash(password: str) -> str:
        seen.append(connections_in_use)
        return hash_password(password)

    def watched_verify(password: str, hashed: str) -> bool:
        seen.append(connections_in_use)
        return verify_password(password, hashed)

    monkeypatch.setattr(security, "hash_password", watched_hash)
    monkeypatch.setattr(security, "verify_password", watched_verify)

    assert client.post(f"{AUTH}/register", json=AYSE).status_code == 201
    assert log_in(client).status_code == 200
    assert seen == [0, 0]  # no connection was held while hashing, nor while verifying


def test_log_in_gives_a_bearer_token(client: TestClient) -> None:
    client.post(f"{AUTH}/register", json=AYSE)
    response = log_in(client, email="AYSE@example.com")  # the e-mail is not case sensitive
    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer"
    assert security.decode_access_token(token["access_token"]) == 1


@pytest.mark.parametrize(
    ("email", "password"),
    [("ayse@example.com", "wrong-password"), ("nobody@example.com", "margherita-4ever")],
)
def test_wrong_password_and_unknown_email_look_the_same(
    client: TestClient, email: str, password: str
) -> None:
    client.post(f"{AUTH}/register", json=AYSE)
    response = log_in(client, email=email, password=password)
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_me_needs_a_valid_token(client: TestClient, ayse: dict[str, str]) -> None:
    assert client.get(ME, headers=ayse).json()["email"] == "ayse@example.com"

    missing = client.get(ME)
    assert missing.status_code == 401
    assert missing.json()["code"] == "NOT_AUTHENTICATED"
    assert missing.headers["WWW-Authenticate"] == "Bearer"

    forged = jwt.encode({"sub": "1"}, "somebody-else's-secret-key-0123456789", algorithm="HS256")
    for token in ("not-a-token", forged):
        assert client.get(ME, headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_an_expired_token_is_refused(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    client.post(f"{AUTH}/register", json=AYSE)
    monkeypatch.setattr(settings, "access_token_expire_minutes", -1)
    expired = log_in(client).json()["access_token"]
    assert client.get(ME, headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_orders_placed_while_logged_in_are_kept_under_me(
    client: TestClient, ayse: dict[str, str], make_pizza: MakePizza
) -> None:
    pizza = make_pizza()
    body = {"pizza_id": pizza["id"], "customer_name": "Ayşe"}
    mine = client.post(ORDERS, json=body, headers=ayse).json()
    guest = client.post(ORDERS, json=body | {"customer_name": "Can"}).json()

    assert mine["user_id"] == 1
    assert guest["user_id"] is None
    assert client.get(f"{ME}/orders", headers=ayse).json() == [mine]
    assert len(client.get(ORDERS).json()) == 2  # the kitchen still sees every order
    assert client.get(f"{ME}/orders").status_code == 401


def test_a_broken_token_does_not_turn_into_a_guest_order(
    client: TestClient, make_pizza: MakePizza
) -> None:
    pizza = make_pizza()
    response = client.post(
        ORDERS,
        json={"pizza_id": pizza["id"], "customer_name": "Ayşe"},
        headers={"Authorization": "Bearer not-a-token"},
    )
    assert response.status_code == 401
    assert client.get(ORDERS).json() == []
