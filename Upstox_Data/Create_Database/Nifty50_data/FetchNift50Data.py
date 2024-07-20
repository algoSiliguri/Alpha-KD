import json
import os
from Upstox_Data.Create_Database.historical_data_fetcher import HistoricalDataFetcher

def write_to_csv(output_dir, interval):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for key, value in nifty50_dict.items():
        df_rates = fetcher.get_rates(value, interval=interval)
        # Define the output file name using the key
        output_file = os.path.join(output_dir, f"{key}_{output_dir}.csv")
        # Save the DataFrame to a CSV file
        df_rates.to_csv(output_file)


class Nifty50Fetcher:
    def __init__(self, json_file):
        self.json_file = json_file
        self.nifty_50_symbols = [
            "HDFCBANK",
            "RELIANCE",
            "ICICIBANK",
            "INFY",
            "LT",
            "TCS",
            "ITC",
            "BHARTIARTL",
            "AXISBANK",
            "SBIN",
            "M&M",
            "KOTAKBANK",
            "HINDUNILVR",
            "BAJFINANCE",
            "NTPC",
            "TATAMOTORS",
            "SUNPHARMA",
            "MARUTI",
            "HCLTECH",
            "POWERGRID",
            "TATASTEEL",
            "TITAN",
            "ULTRACEMCO",
            "ASIANPAINT",
            "ADANIPORTS",
            "COALINDIA",
            "ONGC",
            "BAJAJ-AUTO",
            "HINDALCO",
            "GRASIM",
            "INDUSINDBK",
            "NESTLEIND",
            "TECHM",
            "JSWSTEEL",
            "BAJAJFINSV",
            "ADANIENT",
            "SHRIRAMFIN",
            "CIPLA",
            "DRREDDY",
            "HEROMOTOCO",
            "WIPRO",
            "TATACONSUM",
            "SBILIFE",
            "BRITANNIA",
            "EICHERMOT",
            "APOLLOHOSP",
            "HDFCLIFE",
            "BPCL",
            "DIVISLAB",
            "LTIM"
        ]
        self.data = self.load_json()

    def load_json(self):
        with open(self.json_file, 'r') as file:
            return json.load(file)

    def get_nifty50_values(self):
        result = {}
        for item in self.data:
            for key, value in item.items():
                if key in self.nifty_50_symbols:
                    result[key] = value
        return result


if __name__ == "__main__":
    fetcher = HistoricalDataFetcher()
    raw_json = Nifty50Fetcher('instrumentsData.json')
    nifty50_dict = raw_json.get_nifty50_values()

    # to create monthly data, uncomment below line
    # write_to_csv("Monthly", "month")

    # to create weekly data, uncomment below line
    # write_to_csv("Weekly", "week")

    # to create daily data, uncomment below line
    # write_to_csv("Daily", "day")

