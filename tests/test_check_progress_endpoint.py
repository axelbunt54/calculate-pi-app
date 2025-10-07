"""Tests for /check_progress endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.schemas import ProgressResponse


def test_check_progress_task_not_found(test_client: TestClient) -> None:
    """Endpoint returns 404 for non-existent task."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "PENDING"
        mock_task.info = None
        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "non-existent-id"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Task not found" in data["detail"]


def test_check_progress_task_in_progress(test_client: TestClient) -> None:
    """Endpoint returns PROGRESS state for running task."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "PROGRESS"
        mock_task.info = {"progress": 0.35}
        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "running-task-id"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "PROGRESS"
        assert data["progress"] == 0.35
        assert data["result"] is None


def test_check_progress_task_started(test_client: TestClient) -> None:
    """Endpoint handles STARTED state."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "STARTED"
        mock_task.info = {"progress": 0.0}
        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "started-task-id"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "PROGRESS"
        assert data["progress"] == 0.0


def test_check_progress_task_success(test_client: TestClient) -> None:
    """Endpoint returns FINISHED state for completed task."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "SUCCESS"
        mock_task.result = {"result": "3.14159265358979"}
        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "completed-task-id"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "FINISHED"
        assert data["progress"] == 1.0
        assert data["result"] == "3.14159265358979"


def test_check_progress_task_failure(test_client: TestClient) -> None:
    """Endpoint returns 500 for failed task."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "FAILURE"
        mock_task.info = Exception("Division by zero")
        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "failed-task-id"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Task execution failed" in data["detail"]


def test_check_progress_task_with_no_info(test_client: TestClient) -> None:
    """Endpoint handles task with no metadata."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "PROGRESS"
        mock_task.info = None
        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "no-info-task-id"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "PROGRESS"
        assert data["progress"] == 0.0  # Default value
        assert data["result"] is None


def test_check_progress_empty_task_id(test_client: TestClient) -> None:
    """Endpoint accepts empty string as task_id."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "PENDING"
        mock_task.info = None
        mock_result.return_value = mock_task

        response = test_client.post("/check_progress", json={"task_id": ""})

        # Empty string is valid, should check backend and return 404
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_check_progress_missing_task_id(test_client: TestClient) -> None:
    """Endpoint rejects missing task_id."""
    response = test_client.post("/check_progress", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_check_progress_celery_exception(test_client: TestClient) -> None:
    """Endpoint handles unexpected Celery exceptions."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_result.side_effect = Exception("Redis connection lost")

        response = test_client.post(
            "/check_progress", json={"task_id": "any-task-id"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to check task progress" in data["detail"]


def test_check_progress_response_schema(test_client: TestClient) -> None:
    """Endpoint response matches ProgressResponse schema."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = "PROGRESS"
        mock_task.info = {"progress": 0.75}
        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "schema-test-id"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Validate against schema
        validated = ProgressResponse(**data)
        assert validated.state in ["PROGRESS", "FINISHED"]
        assert 0.0 <= validated.progress <= 1.0


@pytest.mark.parametrize(
    "celery_state,expected_api_state,expected_progress",
    [
        ("STARTED", "PROGRESS", 0.0),
        ("PROGRESS", "PROGRESS", 0.5),
        ("SUCCESS", "FINISHED", 1.0),
    ],
)
def test_check_progress_state_mapping(
    test_client: TestClient,
    celery_state: str,
    expected_api_state: str,
    expected_progress: float,
) -> None:
    """Endpoint correctly maps Celery states to API states."""
    with patch("app.main.celery_app.AsyncResult") as mock_result:
        mock_task = MagicMock()
        mock_task.state = celery_state

        if celery_state == "SUCCESS":
            mock_task.result = {"result": "3.14"}
        else:
            mock_task.info = {"progress": expected_progress}

        mock_result.return_value = mock_task

        response = test_client.post(
            "/check_progress", json={"task_id": "state-test"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == expected_api_state
        assert data["progress"] == expected_progress
