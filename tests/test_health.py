from fastapi.testclient import TestClient


def test_root_points_to_the_docs(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_health_is_ok_and_timed(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Process-Time"].endswith("ms")


def test_docs_and_openapi_are_served(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/v1/pizzas/{pizza_id}" in schema["paths"]
    assert "APIKeyHeader" in schema["components"]["securitySchemes"]
    assert "OAuth2PasswordBearer" in schema["components"]["securitySchemes"]
