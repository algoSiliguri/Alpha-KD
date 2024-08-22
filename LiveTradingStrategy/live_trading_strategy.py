import time
import pandas as pd
import ta
import traceback

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
      self.data: pd.DataFrame = None
      self.previous_day_close = previous_day_close
      self.gap = None

  def calculate_vwap(self):
      """
      Calculate VWAP and add it to the DataFrame.
      """
      try:
            self.data['Cumulative_TPV'] = self.data['Close'] * self.data['Volume']
            self.data['Cumulative_Volume'] = self.data['Volume'].cumsum()
            self.data['Cumulative_TPV'] = self.data['Cumulative_TPV'].cumsum()
            
            # Calculate VWAP
            self.data['VWAP'] = self.data['Cumulative_TPV'] / self.data['Cumulative_Volume']
            
            # Set the VWAP of the first row to be the Close price itself
            self.data.at[self.data.index[0], 'VWAP'] = self.data.at[self.data.index[0], 'Close']

            # Round VWAP to one decimal place
            self.data['VWAP'] = self.data['VWAP'].round(1)
            
            # Drop the intermediate cumulative columns
            self.data.drop(columns=['Cumulative_TPV', 'Cumulative_Volume'], inplace=True)

      except Exception as e:
          print(f"Error calculating VWAP: {e}")

  def check_gap_up(self, i):
    """
    Check for gap up conditions and return a buy signal if conditions are met.

    Args:
        i (int): Current index in the DataFrame.

    Returns:
        bool: True if buy signal is generated, False otherwise.
    """
    try:
        # Do not generate any signal for the first two hours (assuming each row is a minute or hour of trading)
        if i < 4:
            return False

        # Check if the first two hours consistently traded above VWAP
        elif i == 4:
            first_2_hours_above_vwap = all(
                self.data["Close"].iloc[j] >= self.data["VWAP"].iloc[j]
                or (self.data["Close"].iloc[j] < self.data["VWAP"].iloc[j] and 
                    self.data["Close"].iloc[j] >= self.data["VWAP"].iloc[j] - 0.5)
                for j in range(1, 4)
            )
            if first_2_hours_above_vwap:
                return True
        
        # Generate signal if the current close crosses above VWAP after a small dip below VWAP
        elif(self.data["Close"].iloc[i - 1] < self.data["VWAP"].iloc[i - 1] 
            and self.data["Close"].iloc[i] >= self.data["VWAP"].iloc[i]):
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
          # If the price had gone below vwap but came right back up
          if(self.data["Close"].iloc[i - 1] < self.data["VWAP"].iloc[i - 1] 
            and self.data["Close"].iloc[i] >= self.data["VWAP"].iloc[i]):
              
              return True
          else:
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

          print(self.data)

          # Ensure the gap is calculated only once
          if self.gap is None:
              self.gap = (df_intraday_30min["Open"].iloc[0] - self.previous_day_close) / self.previous_day_close * 100
          

          buy = False
          sell = False

          for i in range(len(df_intraday_30min)):
              if self.gap > 3:
                  if self.check_gap_up(i):
                      print("Trade signalled from gap up")
                      buy = True
                      break  # Exit loop after the first buy signal
              elif -1 <= self.gap <= 1:
                  if self.check_flat_open(i):
                      print("Trade signalled from flat open")
                      buy = True
                      break  # Exit loop after the first buy signal
              elif self.gap < -3:
                  if self.check_gap_down(i, self.previous_day_close * 0.97):  # Example stop loss at 3% below previous close
                      print("Trade signalled from gap down")
                      buy = True
                      break  # Exit loop after the first buy signal

          return buy, sell
      except Exception as e:
          traceback.print_exc()
          print(f"Error creating signals: {e}")
          return False, False