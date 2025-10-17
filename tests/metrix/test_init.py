"""Tests for metrix package initialization."""

import metrix


def test_version_exists() -> None:
    """Test that __version__ is defined."""
    assert hasattr(metrix, "__version__")


def test_version_format() -> None:
    """Test that __version__ follows semantic versioning format."""
    version = metrix.__version__
    assert isinstance(version, str)
    assert len(version) > 0
    # Basic semantic versioning check (e.g., "0.1.0")
    parts = version.split(".")
    assert len(parts) >= 2  # noqa: PLR2004  # At least major.minor
    assert all(part.isdigit() or "-" in part for part in parts)  # Allow for pre-release versions


def test_version_value() -> None:
    """Test that __version__ has the expected value."""
    assert metrix.__version__ == "0.1.0"
