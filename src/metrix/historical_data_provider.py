"""Historical data provider for market data using Polygon.io API."""

import hashlib
from pathlib import Path
from typing import ClassVar

import pandas as pd
from loguru import logger
from polygon import RESTClient  # type: ignore[import-untyped]
from pydantic_settings import BaseSettings, SettingsConfigDict


class HistoricalDataProviderConfig(BaseSettings):
    """Configuration for HistoricalDataProvider."""

    ENV_COMMON_PREFIX: ClassVar[str] = "METRIX_"

    polygon_api_key: str
    cache_dir: Path = Path(".cache/historical_data")
    use_cache: bool = True

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

        # Create cache directory if it doesn't exist
        if self.config.use_cache:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Cache directory created at {cache_dir}", cache_dir=self.config.cache_dir)

        logger.debug("Polygon client initialized")

    def _generate_cache_key(  # noqa: PLR0913
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        from_date: str,
        to_date: str,
        adjusted: bool,
        sort: str,
        limit: int,
    ) -> str:
        """Generate a unique cache key for the given parameters.

        Args:
            ticker: Stock ticker symbol
            multiplier: Size of the time window
            timespan: Size of the time window
            from_date: Start date
            to_date: End date
            adjusted: Whether to adjust for splits and dividends
            sort: Sort order
            limit: Maximum number of results

        Returns:
            Hash string to use as cache key
        """
        key_parts = f"{ticker}_{multiplier}_{timespan}_{from_date}_{to_date}_{adjusted}_{sort}_{limit}"
        return hashlib.sha256(key_parts.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the full path for a cache file.

        Args:
            cache_key: The cache key hash

        Returns:
            Path object for the cache file
        """
        return self.config.cache_dir / f"{cache_key}.parquet"

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

        # Check cache first
        if self.config.use_cache:
            cache_key = self._generate_cache_key(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_date=from_date,
                to_date=to_date,
                adjusted=adjusted,
                sort=sort,
                limit=limit,
            )
            cache_path = self._get_cache_path(cache_key)

            if cache_path.exists():
                logger.debug("Loading data from cache: {cache_path}", cache_path=cache_path)
                df = pd.read_parquet(cache_path)
                logger.debug("Loaded {rows} rows from cache", rows=len(df))
                return df

            logger.debug("Cache miss, fetching from API")

        # Fetch from API
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

        # Save to cache
        if self.config.use_cache:
            df.to_parquet(cache_path)
            logger.debug("Saved data to cache: {cache_path}", cache_path=cache_path)

        return df
