import pandas as pd
import ta

class TradingStrategy:
  """
  A class to implement a trading strategy based on intraday data and VWAP.

  Attributes:
      data (pd.DataFrame): DataFrame to store intraday data.
      previous_day_close (float): The closing price of the previous day.
      gap (float): The percentage gap between the previous day's close and the current day's open.
  """

  def __init__(self, previous_day_close):
      """
      Initialize the TradingStrategy with the previous day's closing price.

      Args:
          previous_day_close (float): The closing price of the previous day.
      """
      self.data = None
      self.previous_day_close = previous_day_close
      self.gap = None

  def calculate_vwap(self):
      """
      Calculate VWAP and add it to the DataFrame.
      """
      try:
          self.data["VWAP"] = ta.volume.volume_weighted_average_price(
              self.data["High"], self.data["Low"], self.data["Close"], self.data["Volume"]
          )
      except Exception as e:
          print(f"Error calculating VWAP: {e}")

  def check_gap_up(self, i):
      """
      Check for gap up conditions and return buy signal if conditions are met.

      Args:
          i (int): Current index in the DataFrame.

      Returns:
          bool: True if buy signal is generated, False otherwise.
      """
      try:
          if i < 3:
              return False  # Do not generate any buy/sell signal for the first 2 hours

          else:

              if i == 3:
                  first_2_hours_above_vwap = all(self.data["Close"].iloc[j] >= self.data["VWAP"].iloc[j] for j in range(3))
                  if first_2_hours_above_vwap:
                      return True
              else:
                  if self.data["Close"].iloc[i - 1] < self.data["VWAP"].iloc[i - 1] and self.data["Close"].iloc[i] >= \
                          self.data["VWAP"].iloc[i]:
                      return True
          return False
      except Exception as e:
          print(f"Error checking gap up: {e}")
          return False

  def check_flat_open(self, i):
      """
      Check for flat open conditions and return buy signal if conditions are met.

      Args:
          i (int): Current index in the DataFrame.

      Returns:
          bool: True if buy signal is generated, False otherwise.
      """
      try:
          if self.data["Close"].iloc[i] >= self.data["VWAP"].iloc[i]:
              return True
          return False
      except Exception as e:
          print(f"Error checking flat open: {e}")
          return False

  def check_gap_down(self, i, stop_loss):
      """
      Check for gap down conditions and return buy signal if conditions are met.

      Args:
          i (int): Current index in the DataFrame.
          stop_loss (float): The stop loss price point.

      Returns:
          bool: True if buy signal is generated, False otherwise.
      """
      try:
          if self.data["Close"].iloc[i] < stop_loss:
              return False  # Wait if the price is below the stop loss point
          if self.data["Close"].iloc[i] >= stop_loss and self.data["Close"].iloc[i] >= self.data["VWAP"].iloc[i]:
              return True
          return False
      except Exception as e:
          print(f"Error checking gap down: {e}")
          return False

  def create_signals(self, df_intraday_30min):
      """
      Create buy and sell signals based on the strategy logic.

      Args:
          df_intraday_30min (pd.DataFrame): DataFrame containing live intraday data appended every 30 minutes.

      Returns:
          tuple: Tuple of buy and sell signals (buy, sell).
      """
      try:
          # Update the data attribute with the new intraday data
          self.data = df_intraday_30min

          # Calculate VWAP for the updated data
          self.calculate_vwap()

          # Ensure the gap is calculated only once
          if self.gap is None:
              self.gap = (df_intraday_30min["Open"].iloc[0] - self.previous_day_close) / self.previous_day_close * 100

          buy = False
          sell = False

          for i in range(len(df_intraday_30min)):
              if self.gap > 3:
                  if self.check_gap_up(i):
                      buy = True
                      break  # Exit loop after the first buy signal
              elif -1 <= self.gap <= 1:
                  if self.check_flat_open(i):
                      buy = True
                      break  # Exit loop after the first buy signal
              elif self.gap < -3:
                  if self.check_gap_down(i, self.previous_day_close * 0.97):  # Example stop loss at 3% below previous close
                      buy = True
                      break  # Exit loop after the first buy signal

          return buy, sell
      except Exception as e:
          print(f"Error creating signals: {e}")
          return False, False