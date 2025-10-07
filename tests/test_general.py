from fastapi import status
from fastapi.testclient import TestClient


def test_root_redirects_to_docs(test_client: TestClient) -> None:
    response = test_client.get("/", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers.get("location") == "/docs"


def test_docs_ui_served(test_client: TestClient) -> None:
    response = test_client.get("/docs")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")
    assert "Swagger UI" in response.text


def test_openapi_schema_available(test_client: TestClient) -> None:
    response = test_client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert data.get("openapi", "").startswith("3.")
    assert "/calculate_pi" in data.get("paths", {})
    assert "/check_progress" in data.get("paths", {})
