from historical_data_fetcher import HistoricalDataFetcher

# Example usage
fetcher = HistoricalDataFetcher()

symbol = "NSE_EQ|INE848E01016"
df_rates = fetcher.get_rates(symbol, interval="1minute")
print(df_rates)


print("HIIIIIIIIIII")