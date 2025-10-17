"""Tests for HistoricalDataProvider."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from metrix.historical_data_provider import HistoricalDataProvider, HistoricalDataProviderConfig


class TestHistoricalDataProviderConfig:
    """Tests for HistoricalDataProviderConfig."""

    def test_config_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test config initialization from environment variables."""
        monkeypatch.setenv("METRIX_POLYGON_API_KEY", "test_api_key_123")
        config = HistoricalDataProviderConfig()  # type: ignore[call-arg]
        assert config.polygon_api_key == "test_api_key_123"

    def test_config_explicit(self) -> None:
        """Test config initialization with explicit values."""
        config = HistoricalDataProviderConfig(polygon_api_key="explicit_key")
        assert config.polygon_api_key == "explicit_key"


class TestHistoricalDataProvider:
    """Tests for HistoricalDataProvider."""

    @pytest.fixture
    def mock_config(self) -> HistoricalDataProviderConfig:
        """Create a mock configuration."""
        return HistoricalDataProviderConfig(polygon_api_key="test_key")

    @pytest.fixture
    def provider(self, mock_config: HistoricalDataProviderConfig) -> HistoricalDataProvider:
        """Create a HistoricalDataProvider instance."""
        return HistoricalDataProvider(config=mock_config)

    def test_init_with_config(self, mock_config: HistoricalDataProviderConfig) -> None:
        """Test initialization with explicit config."""
        provider = HistoricalDataProvider(config=mock_config)
        assert provider.config == mock_config
        assert provider.polygon_client is not None

    def test_init_without_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization without config (should load from env)."""
        monkeypatch.setenv("METRIX_POLYGON_API_KEY", "env_key")
        provider = HistoricalDataProvider()
        assert provider.config.polygon_api_key == "env_key"
        assert provider.polygon_client is not None

    def test_get_historical_data(self, provider: HistoricalDataProvider) -> None:
        """Test get_historical_data method."""
        # Create mock aggregates
        mock_agg1 = MagicMock()
        mock_agg1.open = 150.0
        mock_agg1.high = 152.0
        mock_agg1.low = 149.0
        mock_agg1.close = 151.0
        mock_agg1.volume = 1000000
        mock_agg1.vwap = 150.5
        mock_agg1.timestamp = 1609459200000  # 2021-01-01 00:00:00 UTC
        mock_agg1.transactions = 100

        mock_agg2 = MagicMock()
        mock_agg2.open = 151.0
        mock_agg2.high = 153.0
        mock_agg2.low = 150.0
        mock_agg2.close = 152.0
        mock_agg2.volume = 1100000
        mock_agg2.vwap = 151.5
        mock_agg2.timestamp = 1609459800000  # 2021-01-01 00:10:00 UTC
        mock_agg2.transactions = 110

        # Setup mock client
        mock_client = MagicMock()
        mock_client.list_aggs.return_value = iter([mock_agg1, mock_agg2])
        provider.polygon_client = mock_client

        # Call the method
        df = provider.get_historical_data(
            ticker="AAPL",
            multiplier=10,
            timespan="minute",
            from_date="2021-01-01",
            to_date="2021-01-02",
            adjusted=True,
            sort="asc",
            limit=50000,
        )

        # Verify the client was called correctly
        mock_client.list_aggs.assert_called_once_with(
            ticker="AAPL",
            multiplier=10,
            timespan="minute",
            from_="2021-01-01",
            to="2021-01-02",
            adjusted="true",
            sort="asc",
            limit=50000,
        )

        # Verify the DataFrame
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # noqa: PLR2004
        assert list(df.columns) == ["open", "high", "low", "close", "volume", "vwap", "timestamp", "transactions"]

        # Check first row
        assert df.iloc[0]["open"] == 150.0  # noqa: PLR2004
        assert df.iloc[0]["high"] == 152.0  # noqa: PLR2004
        assert df.iloc[0]["low"] == 149.0  # noqa: PLR2004
        assert df.iloc[0]["close"] == 151.0  # noqa: PLR2004
        assert df.iloc[0]["volume"] == 1000000  # noqa: PLR2004
        assert df.iloc[0]["vwap"] == 150.5  # noqa: PLR2004
        assert df.iloc[0]["transactions"] == 100  # noqa: PLR2004

        # Check second row
        assert df.iloc[1]["open"] == 151.0  # noqa: PLR2004
        assert df.iloc[1]["close"] == 152.0  # noqa: PLR2004

    def test_get_historical_data_empty(self, provider: HistoricalDataProvider) -> None:
        """Test get_historical_data with no results."""
        mock_client = MagicMock()
        mock_client.list_aggs.return_value = iter([])
        provider.polygon_client = mock_client

        df = provider.get_historical_data(
            ticker="INVALID",
            multiplier=1,
            timespan="day",
            from_date="2021-01-01",
            to_date="2021-01-02",
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
