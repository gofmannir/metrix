
from metrix.historical_data_provider import HistoricalDataProvider
from loguru import logger

import pandas as pd

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 320)
pd.set_option("display.float_format", "{:.3f}".format)

def main():
    history_provider = HistoricalDataProvider()
    data = history_provider.get_historical_data(
        ticker="AAPL",
        multiplier=1,
        timespan="day",
        from_date="2025-10-10",
        to_date="2025-10-17",
    )
    logger.info("Retrieved data:\n{data}", data=data)

if __name__ == "__main__":
    main()