import pandas as pd
from datetime import datetime

class IntradayDataAppender:
  """
  A class to fetch and append intraday OHLC data to a DataFrame using the Upstox API.

  Attributes:
      upstox_api_live_instance (UpstoxAPILive): An instance of the UpstoxAPILive class.
      df (pd.DataFrame): A DataFrame to store the OHLC data.
  """

  def __init__(self, upstox_api_live_instance):
      """
      Initializes the IntradayDataAppender with an UpstoxAPILive instance.

      Args:
          upstox_api_live_instance (UpstoxAPILive): An instance of the UpstoxAPILive class.
      """
      self.upstox_api_live_instance = upstox_api_live_instance
      self.df = pd.DataFrame(columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])

  def append_data_to_dataframe(self, symbol, interval="30minute", initial_run = False):
      """
      Fetches intraday OHLC data for a given symbol and interval, and appends it to the DataFrame.

      Args:
          symbol (str): The trading symbol.
          interval (str): The timeframe for the data (default is "30minute").

      Raises:
          Exception: If there is an error fetching the data.
      """
      try:
          data = self.upstox_api_live_instance.get_rates(symbol, interval)

          # For the first time in the day (Revert the data sequence)
          if initial_run:
              data = data[::-1]
              
          if data:
              for candle in data:
                  timestamp = datetime.fromisoformat(candle[0])
                  if not self.df[self.df['timestamp'] == timestamp].empty:
                      continue  # Skip if the timestamp already exists in the DataFrame

                  open_price = candle[1]
                  high_price = candle[2]
                  low_price = candle[3]
                  close_price = candle[4]
                  volume = candle[5]

                  self.df.loc[len(self.df)] = {
                                                'timestamp': timestamp,
                                                'Open': open_price,
                                                'High': high_price,
                                                'Low': low_price,
                                                'Close': close_price,
                                                'Volume': volume
                                                }

      except Exception as e:
          print(f"Error appending data to DataFrame: {e}")

  def get_dataframe(self):
      """
      Returns the DataFrame containing the OHLC data.

      Returns:
          pd.DataFrame: The DataFrame containing the OHLC data.
      """
      return self.df

# # Example usage
# if __name__ == "__main__":
#   try:
#       access_token = "your_access_token"
#       upstox_api_live_instance = UpstoxAPILive(access_token)
#
#       appender = IntradayDataAppender(upstox_api_live_instance)
#       symbol = "your_symbol"
#       appender.append_data_to_dataframe(symbol)
#       df = appender.get_dataframe()
#       print(df)
#   except Exception as e:
#       print(f"Error in main execution: {e}")