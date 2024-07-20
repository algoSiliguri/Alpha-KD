from datetime import datetime, timedelta
from upstox_api import UpstoxAPI
from data_processor import DataProcessor
import pandas as pd


class HistoricalDataFetcher:
    """A class to fetch and process historical data from the Upstox API."""

    def __init__(self):
        self.api_client = UpstoxAPI
        self.data_processor = DataProcessor

    def get_rates(
        self, symbol: str, number_of_data: int = 10_000, interval: str = "day"
    ) -> pd.DataFrame:
        """
        Fetch and process historical data for a given symbol and interval.

        Args:
            symbol (str): The symbol for which to fetch historical data.
            number_of_data (int, optional): The number of data points to fetch. Defaults to 10,000.
            interval (str, optional): The interval for the historical data. Defaults to "day".

        Returns:
            pd.DataFrame: A pandas DataFrame with the processed historical data.

        Raises:
            ValueError: If an invalid interval is provided.
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        if interval in ["1minute", "30minute"]:
            # For 1-minute and 30-minute intervals, data is available for the preceding six months
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        elif interval in ["day", "week", "month"]:
            # For day, week, and month intervals, data is available for the preceding 20 years
            start_date = (datetime.now() - timedelta(days=365 * 20)).strftime(
                "%Y-%m-%d"
            )
        else:
            raise ValueError(
                "Invalid interval. Choose from '1minute', '30minute', 'day', 'week', 'month'."
            )

        candles = self.api_client.get_historical_data(
            symbol, interval, start_date, end_date
        )
        return self.data_processor.process_candle_data(candles)
