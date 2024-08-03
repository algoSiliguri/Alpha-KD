import json
from typing import Dict, List


class SymbolFetcher:
    """
    SymbolFetcher is responsible for loading symbol data from a JSON file and fetching specific symbol values.

    Attributes:
        json_file (str): The path to the JSON file containing symbol data.
        symbols (List[str]): A list of symbols to fetch values for. If None, all symbols are fetched.
        data (List[Dict]): The loaded JSON data.
    """

    def __init__(self, json_file: str, symbols: List[str] = None):
        """
        Initializes the SymbolFetcher with a JSON file and an optional list of symbols.

        Args:
            json_file (str): The path to the JSON file containing symbol data.
            symbols (List[str], optional): A list of symbols to fetch values for. Defaults to None.
        """
        self.json_file = json_file
        self.symbols = symbols
        self.data = self.load_json()

    def load_json(self) -> List[Dict]:
        """
        Loads the JSON data from the specified file.

        Returns:
            List[Dict]: The loaded JSON data.

        Raises:
            IOError: If there is an error reading the JSON file.
            json.JSONDecodeError: If there is an error decoding the JSON file.
        """
        try:
            with open(self.json_file, "r") as file:
                return json.load(file)
        except IOError as e:
            print(f"Error reading JSON file {self.json_file}: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON file {self.json_file}: {e}")
            raise

    def get_values(self) -> Dict[str, str]:
        """
        Fetches the values for the specified symbols from the loaded JSON data.

        Returns:
            Dict[str, str]: A dictionary of symbol-value pairs.

        Raises:
            KeyError: If a specified symbol is not found in the JSON data.
        """
        try:
            if not self.symbols:
                return {key: value for item in self.data for key, value in item.items()}

            result = {}
            for item in self.data:
                for key, value in item.items():
                    if key in self.symbols:
                        result[key] = value
            return result
        except KeyError as e:
            print(f"Error fetching values for symbols: {e}")
            raise
