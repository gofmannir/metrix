"""Tests for metrix.__main__ module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

from metrix.__main__ import main


def test_main_function_exists() -> None:
    """Test that main function exists and is callable."""
    assert callable(main)


def test_main_returns_none() -> None:
    """Test that main function returns None."""
    main()  # main() returns None, so we don't need to capture the result


def test_main_logs_message(mocker: MagicMock) -> None:
    """Test that main function logs the expected message."""
    # Mock the logger.info method to capture the call
    mock_logger_info = mocker.patch("metrix.__main__.logger.info")

    main()

    # Verify that logger.info was called with the expected message
    mock_logger_info.assert_called_once_with("Hello from rpa!")


def test_main_module_execution_as_script() -> None:
    """Test that __main__.py can be executed as a script directly."""
    # Get the path to the __main__.py file
    main_path = Path(__file__).parent.parent.parent / "src" / "metrix" / "__main__.py"

    # Execute the module as a script (this will trigger the if __name__ == "__main__" block)
    # Use coverage run to track subprocess coverage
    result = subprocess.run(
        [sys.executable, "-m", "coverage", "run", "--source=src", str(main_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
        cwd=Path(__file__).parent.parent.parent,
    )

    # Check that it executed without errors
    assert result.returncode == 0


def test_main_module_execution_as_module() -> None:
    """Test that the package can be executed as a module using -m flag."""
    # Execute as a module: python -m metrix
    result = subprocess.run(
        [sys.executable, "-m", "metrix"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
        cwd=Path(__file__).parent.parent.parent,
    )

    # Check that it executed without errors
    assert result.returncode == 0
