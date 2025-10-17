"""Historical data provider for market data using Polygon.io API."""

from typing import ClassVar

import pandas as pd
from loguru import logger
from polygon import RESTClient  # type: ignore[import-untyped]
from pydantic_settings import BaseSettings, SettingsConfigDict


class HistoricalDataProviderConfig(BaseSettings):
    """Configuration for HistoricalDataProvider."""

    ENV_COMMON_PREFIX: ClassVar[str] = "METRIX_"

    polygon_api_key: str

    model_config = SettingsConfigDict(
        env_prefix=ENV_COMMON_PREFIX,
        env_file=".env",
        extra="ignore",
    )


class HistoricalDataProvider:
    """Provider for historical market data from Polygon.io."""

    def __init__(self, config: HistoricalDataProviderConfig | None = None) -> None:
        """Initialize the historical data provider.

        Args:
            config: Configuration object. If None, will be loaded from environment variables.
        """
        self.config = config if config is not None else HistoricalDataProviderConfig()  # type: ignore[call-arg]
        logger.debug("Initializing HistoricalDataProvider with config={config}", config=self.config)
        self.polygon_client = RESTClient(self.config.polygon_api_key)
        logger.debug("Polygon client initialized")

    def get_historical_data(  # noqa: PLR0913
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        from_date: str,
        to_date: str,
        adjusted: bool = True,
        sort: str = "asc",
        limit: int = 50000,
    ) -> pd.DataFrame:
        """Retrieve historical market data for a given ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            multiplier: Size of the time window (e.g., 1 for 1 minute, 5 for 5 minutes)
            timespan: Size of the time window (e.g., "minute", "hour", "day")
            from_date: Start date in format "YYYY-MM-DD"
            to_date: End date in format "YYYY-MM-DD"
            adjusted: Whether to adjust for splits and dividends
            sort: Sort order - "asc" or "desc"
            limit: Maximum number of results to return

        Returns:
            DataFrame with columns: open, high, low, close, volume, vwap, timestamp, transactions
        """
        logger.debug(
            "Fetching historical data: ticker={ticker}, multiplier={multiplier}, timespan={timespan}, "
            "from_date={from_date}, to_date={to_date}, adjusted={adjusted}, sort={sort}, limit={limit}",
            ticker=ticker,
            multiplier=multiplier,
            timespan=timespan,
            from_date=from_date,
            to_date=to_date,
            adjusted=adjusted,
            sort=sort,
            limit=limit,
        )

        aggs = []
        for agg in self.polygon_client.list_aggs(
            ticker=ticker,
            multiplier=multiplier,
            timespan=timespan,
            from_=from_date,
            to=to_date,
            adjusted=str(adjusted).lower(),
            sort=sort,
            limit=limit,
        ):
            aggs.append(agg)

        logger.debug("Retrieved {count} aggregates", count=len(aggs))

        df = pd.DataFrame(
            [
                {
                    "open": agg.open,
                    "high": agg.high,
                    "low": agg.low,
                    "close": agg.close,
                    "volume": agg.volume,
                    "vwap": agg.vwap,
                    "timestamp": pd.to_datetime(agg.timestamp, unit="ms", utc=True),
                    "transactions": agg.transactions,
                }
                for agg in aggs
            ]
        )

        logger.debug("Created DataFrame with {rows} rows", rows=len(df))
        return df
