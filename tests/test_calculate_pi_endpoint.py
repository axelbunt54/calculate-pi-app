"""Tests for /calculate_pi endpoint."""

from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.schemas import CalculatePiResponse


def test_calculate_pi_minimal_value(test_client: TestClient) -> None:
    """Endpoint accepts n=1."""
    with patch("app.main.calculate_pi_task.delay") as mock_delay:
        mock_task = MagicMock()
        mock_task.id = "test-task-id-123"
        mock_delay.return_value = mock_task

        response = test_client.post("/calculate_pi", json={"n": 1})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["task_id"] == "test-task-id-123"
        assert "1 digits" in data["message"]
        mock_delay.assert_called_once_with(1)


def test_calculate_pi_typical_value(test_client: TestClient) -> None:
    """Endpoint accepts typical n=100."""
    with patch("app.main.calculate_pi_task.delay") as mock_delay:
        mock_task = MagicMock()
        mock_task.id = "task-uuid-456"
        mock_delay.return_value = mock_task

        response = test_client.post("/calculate_pi", json={"n": 100})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["task_id"] == "task-uuid-456"
        assert "100 digits" in data["message"]
        mock_delay.assert_called_once_with(100)


def test_calculate_pi_large_value(test_client: TestClient) -> None:
    """Endpoint accepts large n=10000."""
    with patch("app.main.calculate_pi_task.delay") as mock_delay:
        mock_task = MagicMock()
        mock_task.id = "large-task-id"
        mock_delay.return_value = mock_task

        response = test_client.post("/calculate_pi", json={"n": 10000})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["task_id"] == "large-task-id"
        assert "10000 digits" in data["message"]


def test_calculate_pi_rejects_zero(test_client: TestClient) -> None:
    """Endpoint rejects n=0."""
    response = test_client.post("/calculate_pi", json={"n": 0})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_calculate_pi_rejects_negative(test_client: TestClient) -> None:
    """Endpoint rejects negative n."""
    response = test_client.post("/calculate_pi", json={"n": -10})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_calculate_pi_rejects_float(test_client: TestClient) -> None:
    """Endpoint rejects float n."""
    response = test_client.post("/calculate_pi", json={"n": 3.14})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_calculate_pi_coerces_valid_string(test_client: TestClient) -> None:
    """Endpoint coerces valid numeric string to int."""
    with patch("app.main.calculate_pi_task.delay") as mock_delay:
        mock_task = MagicMock()
        mock_task.id = "string-coercion-task"
        mock_delay.return_value = mock_task

        response = test_client.post("/calculate_pi", json={"n": "100"})
        assert response.status_code == status.HTTP_200_OK
        mock_delay.assert_called_once_with(100)


def test_calculate_pi_rejects_invalid_string(test_client: TestClient) -> None:
    """Endpoint rejects non-numeric string."""
    response = test_client.post("/calculate_pi", json={"n": "abc"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_calculate_pi_missing_parameter(test_client: TestClient) -> None:
    """Endpoint rejects missing n parameter."""
    response = test_client.post("/calculate_pi", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_calculate_pi_task_creation_error(test_client: TestClient) -> None:
    """Endpoint handles Celery task creation errors."""
    with patch("app.main.calculate_pi_task.delay") as mock_delay:
        mock_delay.side_effect = Exception("Celery connection failed")

        response = test_client.post("/calculate_pi", json={"n": 100})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "Failed to start calculation" in data["detail"]


def test_calculate_pi_response_schema(test_client: TestClient) -> None:
    """Endpoint response matches CalculatePiResponse schema."""
    with patch("app.main.calculate_pi_task.delay") as mock_delay:
        mock_task = MagicMock()
        mock_task.id = "schema-test-id"
        mock_delay.return_value = mock_task

        response = test_client.post("/calculate_pi", json={"n": 50})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Validate against schema
        validated = CalculatePiResponse(**data)
        assert validated.task_id == "schema-test-id"
        assert isinstance(validated.message, str)


def test_calculate_pi_returns_unique_task_ids(test_client: TestClient) -> None:
    """Endpoint returns different task_id for each request."""
    with patch("app.main.calculate_pi_task.delay") as mock_delay:
        task_ids = []
        for i in range(3):
            mock_task = MagicMock()
            mock_task.id = f"task-{i}"
            mock_delay.return_value = mock_task

            response = test_client.post("/calculate_pi", json={"n": 10})
            assert response.status_code == status.HTTP_200_OK
            task_ids.append(response.json()["task_id"])

        assert len(set(task_ids)) == 3  # All unique
