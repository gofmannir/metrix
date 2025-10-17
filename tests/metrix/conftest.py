"""Pytest configuration and fixtures for metrix tests."""

import pytest
from loguru import logger


@pytest.fixture(autouse=True)
def _reset_loguru() -> None:
    """Reset loguru configuration before each test to avoid interference."""
    # Remove all handlers and re-add stderr with a consistent format
    logger.remove()
    logger.add(
        lambda _: None,  # Sink that does nothing - tests can use caplog
        format="{message}",
        level="DEBUG",
    )


@pytest.fixture
def sample_version() -> str:
    """Provide a sample version string for testing."""
    return "0.1.0"
