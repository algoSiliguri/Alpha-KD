import requests
from typing import List, Dict, Any


class UpstoxAPI:
    """A class to interact with the Upstox API for fetching historical data."""

    BASE_URL = "https://api.upstox.com/v2"

    @staticmethod
    def get_historical_data(
        symbol: str, interval: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical data for a given symbol and interval from the Upstox API.

        Args:
            symbol (str): The symbol for which to fetch historical data.
            interval (str): The interval for the historical data (e.g., '1d', '1h').
            start_date (str): The start date for the historical data in 'YYYY-MM-DD' format.
            end_date (str): The end date for the historical data in 'YYYY-MM-DD' format.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the historical candle data.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
            ValueError: If the API response indicates a failure.
        """
        url = f"{UpstoxAPI.BASE_URL}/historical-candle/{symbol}/{interval}/{end_date}/{start_date}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise requests.exceptions.RequestException(
                f"API request failed with status code {response.status_code}: {response.text}"
            )

        data = response.json()

        if data.get("status") != "success":
            raise ValueError(f"API request failed with status: {data.get('status')}")

        return data.get("data", {}).get("candles", [])
