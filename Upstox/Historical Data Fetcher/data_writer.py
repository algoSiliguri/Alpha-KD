import os
from typing import Dict
from file_manager import FileManager
from historical_data_fetcher import HistoricalDataFetcher


class DataWriter:
    """
    DataWriter is responsible for fetching historical data for given symbols and writing it to CSV files.

    Attributes:
        fetcher (HistoricalDataFetcher): An instance of HistoricalDataFetcher to fetch historical data.
        file_manager (FileManager): An instance of FileManager to handle file operations.
    """

    def __init__(self, fetcher: HistoricalDataFetcher, file_manager: FileManager):
        """
        Initializes the DataWriter with a data fetcher and a file manager.

        Args:
            fetcher (HistoricalDataFetcher): An instance of HistoricalDataFetcher.
            file_manager (FileManager): An instance of FileManager.
        """
        self.fetcher = fetcher
        self.file_manager = file_manager

    def write_to_csv(self, output_dir: str, interval: str, symbols: Dict[str, str]):
        """
        Fetches historical data for the given symbols and writes it to CSV files in the specified output directory.

        Args:
            output_dir (str): The directory where the CSV files will be saved.
            interval (str): The interval for fetching historical data (e.g., '1d', '1h').
            symbols (Dict[str, str]): A dictionary where keys are symbol names and values are their corresponding identifiers.

        Raises:
            Exception: If there is an error in fetching data or writing to CSV.
        """
        try:
            self.file_manager.ensure_directory_exists(output_dir)
        except Exception as e:
            print(f"Error ensuring directory exists: {e}")
            return

        for key, value in symbols.items():
            try:
                df_rates = self.fetcher.get_rates(value, interval=interval)
            except Exception as e:
                print(f"Error fetching data for {value}: {e}")
                continue

            output_file = os.path.join(output_dir, f"{key}_{interval}.csv")
            try:
                self.file_manager.write_to_csv(df_rates, output_file)
            except Exception as e:
                print(f"Error writing data to {output_file}: {e}")
