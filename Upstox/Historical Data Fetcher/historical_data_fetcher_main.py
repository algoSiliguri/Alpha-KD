from symbol_fetcher import SymbolFetcher
from data_writer import DataWriter
from file_manager import FileManager
from historical_data_fetcher import HistoricalDataFetcher


def historical_data_fetcher_main():
    """
    Main function to fetch historical data for specified symbols and write it to CSV files.
    """
    symbols = [
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
        "LTIM",
    ]

    try:
        fetcher = HistoricalDataFetcher()
        raw_json = SymbolFetcher("../../utils/instrumentsData.json", symbols)
        symbol_dict = raw_json.get_values()

        file_manager = FileManager()
        data_writer = DataWriter(fetcher, file_manager)

        # To create monthly data, uncomment below line
        # data_writer.write_to_csv("../../Upstox_Data/Fixed_Time_Bars", "month", symbol_dict)

        # To create weekly data, uncomment below line
        # data_writer.write_to_csv("Weekly", "week", symbol_dict)

        # To create daily data, uncomment below line
        # For Interval Choose from '1minute', '30minute', 'day', 'week', 'month'.
        data_writer.write_to_csv(
            "../../Upstox_Data/Fixed_Time_Bars", "day", symbol_dict
        )

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    historical_data_fetcher_main()
