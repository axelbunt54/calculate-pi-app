import sys
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from loguru import logger

from app.main import app


@pytest.fixture(autouse=True, scope="session")
def _configure_test_logging() -> Iterator[None]:
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    try:
        yield
    finally:
        logger.remove()


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    return TestClient(app)
