import pandas as pd
from typing import List, Dict


class DataProcessor:
    """A class to process candle data into a pandas DataFrame."""

    @staticmethod
    def process_candle_data(candles: List[Dict[str, float]]) -> pd.DataFrame:
        """
        Process a list of candle data into a pandas DataFrame.

        Args:
            candles (List[Dict[str, float]]): A list of dictionaries containing candle data.

        Returns:
            pd.DataFrame: A pandas DataFrame with the processed candle data.
        """
        try:
            df = pd.DataFrame(
                candles,
                columns=[
                    "time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "open_interest",
                ],
            )
            df["time"] = pd.to_datetime(df["time"])
            df = df.set_index("time")
            # Sort the DataFrame by the index to ensure it is in the correct order
            df = df.sort_index()
            return df
        except KeyError as e:
            raise ValueError(f"Missing expected column in candle data: {e}")
        except Exception as e:
            raise ValueError(f"An error occurred while processing candle data: {e}")
