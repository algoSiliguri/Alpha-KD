import pandas as pd
import numpy as np

class DeclineAnalyzer:
  def __init__(self, file_path):
      """
      Initializes the DeclineAnalyzer with the given file path.

      Args:
          file_path (str): The path to the CSV file containing the data.
      """
      self.file_path = file_path
      self.data = None
      self.decline_stats = []

  def load_data(self):
      """
      Load the CSV data with 'time' as the index.

      The method reads the CSV file specified by the file path, sets the 'time' column as the index,
      parses the dates, the DataFrame have the earliest date first.
      """
      self.data = pd.read_csv(self.file_path, index_col='time', parse_dates=True)

  def process_data(self, ema_period=20, std_multiplier=2.0):
      """
      Process the data to calculate percentage change, EMA, and rolling standard deviation.

      Args:
          ema_period (int, optional): The period for calculating the Exponential Moving Average (EMA). Defaults to 20.
          std_multiplier (float, optional): The multiplier for the rolling standard deviation to calculate the threshold. Defaults to 2.0.
      """
      self.data['Pct_Change'] = self.data['close'].pct_change() * 100
      self.data.dropna(inplace=True)
      self.data['Cumulative_Decline'] = 0.0
      self.data['Threshold'] = np.nan
      self.data['Significant'] = 'No'
      self.data['EMA'] = self.data['Pct_Change'].ewm(span=ema_period, adjust=False).mean()
      self.data['Rolling_StdDev'] = self.data['Pct_Change'].rolling(window=ema_period).std()
      self.data.dropna(subset=['EMA', 'Rolling_StdDev'], inplace=True)

  def calculate_threshold(self, index, std_multiplier):
      """
      Calculate the dynamic threshold based on EMA and rolling standard deviation.

      Args:
          index (int): The index of the row for which to calculate the threshold.
          std_multiplier (float): The multiplier for the rolling standard deviation.

      Returns:
          float: The calculated threshold value.
      """
      if not np.isnan(self.data['EMA'].iloc[index]):
          threshold = self.data['EMA'].iloc[index] - std_multiplier * self.data['Rolling_StdDev'].iloc[index]
      else:
          threshold = np.nan
      return threshold

  def update_peak_and_decline(self, i, peak_index, peak_value, cumulative_decline, consecutive_above_peak, std_multiplier):
      """
      Update the peak value and cumulative decline based on the current close price.

      Args:
          i (int): The current index in the DataFrame.
          peak_index (int): The index of the current peak.
          peak_value (float): The value of the current peak.
          cumulative_decline (float): The cumulative decline from the peak.
          consecutive_above_peak (int): The count of consecutive days above the peak.
          std_multiplier (float): The multiplier for the rolling standard deviation.

      Returns:
          tuple: Updated values for peak_index, peak_value, cumulative_decline, and consecutive_above_peak.
      """
      threshold = self.calculate_threshold(i, std_multiplier)
      self.data.at[self.data.index[i], 'Threshold'] = threshold

      if self.data['close'].iloc[i] < peak_value:
          consecutive_above_peak = 0
          cumulative_decline += self.data['Pct_Change'].iloc[i]
      else:
          consecutive_above_peak += 1
          if consecutive_above_peak >= 2:
              peak_index = self.data.index[i]
              peak_value = self.data['close'].iloc[i]
              cumulative_decline = 0.0

      if not np.isnan(threshold) and cumulative_decline <= threshold:
          self.data.at[self.data.index[i], 'Significant'] = 'Yes'
      else:
          self.data.at[self.data.index[i], 'Significant'] = 'No'

      self.data.at[self.data.index[i], 'Cumulative_Decline'] = cumulative_decline

      return peak_index, peak_value, cumulative_decline, consecutive_above_peak

  def load_and_process_data(self, ema_period=20, std_multiplier=2.0):
      """
      Load the data and process it to calculate the Cumulative Decline with a dynamic threshold.

      Args:
          ema_period (int, optional): The period for calculating the Exponential Moving Average (EMA). Defaults to 20.
          std_multiplier (float, optional): The multiplier for the rolling standard deviation to calculate the threshold. Defaults to 2.0.
      """
      self.load_data()
      self.process_data(ema_period, std_multiplier)

      peak_index = self.data.index[0]
      peak_value = self.data['close'].iloc[0]
      cumulative_decline = 0.0
      consecutive_above_peak = 0

      for i in range(1, len(self.data)):
          peak_index, peak_value, cumulative_decline, consecutive_above_peak = self.update_peak_and_decline(
              i, peak_index, peak_value, cumulative_decline, consecutive_above_peak, std_multiplier
          )

  def save_data(self):
      """
      Save the data DataFrame and decline statistics to CSV files.

      The method saves the processed data DataFrame to a CSV file.
      """
      self.data.to_csv('../Market Down Regime Analysis/data.csv')

# Example Usage
# Create an instance of the analyzer with the file path
analyzer = DeclineAnalyzer('../Upstox_Data/Fixed_Time_Bars/NIFTYBEES_day.csv')

# Load and process the data
analyzer.load_and_process_data()

# Optionally, save the full data with cumulative declines
analyzer.save_data()