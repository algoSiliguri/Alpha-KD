import pandas as pd
import numpy as np

class NiftyDeclineAnalyzer:
  def __init__(self, file_path):
      self.file_path = file_path
      self.data = None
      self.decline_stats = []

  def load_data(self):
      """Load the CSV data with Date as the index and reverse the DataFrame."""
      self.data = pd.read_csv(self.file_path, index_col='Date', parse_dates=True)
      self.data = self.data.iloc[::-1]

  def process_data(self, ema_period=20, std_multiplier=2.0):
      """Process the data to calculate percentage change, EMA, and rolling standard deviation."""
      self.data['Pct_Change'] = self.data['Close'].pct_change() * 100
      self.data.dropna(inplace=True)
      self.data['Cumulative_Decline'] = 0.0
      self.data['Threshold'] = np.nan
      self.data['Significant'] = 'No'
      self.data['EMA'] = self.data['Pct_Change'].ewm(span=ema_period, adjust=False).mean()
      self.data['Rolling_StdDev'] = self.data['Pct_Change'].rolling(window=ema_period).std()
      self.data.dropna(subset=['EMA', 'Rolling_StdDev'], inplace=True)

  def calculate_threshold(self, index, std_multiplier):
      """Calculate the dynamic threshold based on EMA and rolling standard deviation."""
      if not np.isnan(self.data['EMA'].iloc[index]):
          # Calculate threshold using EMA and rolling standard deviation
          threshold = self.data['EMA'].iloc[index] - std_multiplier * self.data['Rolling_StdDev'].iloc[index]
      else:
          # If EMA is NaN, return NaN for the threshold
          threshold = np.nan
      return threshold

  def update_peak_and_decline(self, i, peak_index, peak_value, cumulative_decline, consecutive_above_peak,
                              std_multiplier):
      """Update the peak value and cumulative decline based on the current close price."""
      threshold = self.calculate_threshold(i, std_multiplier)
      self.data.at[self.data.index[i], 'Threshold'] = threshold

      if self.data['Close'].iloc[i] < peak_value:
          consecutive_above_peak = 0
          cumulative_decline += self.data['Pct_Change'].iloc[i]
      else:
          consecutive_above_peak += 1
          if consecutive_above_peak >= 2:
              self.analyze_downturn(peak_index, self.data.index[i])
              peak_index = self.data.index[i]
              peak_value = self.data['Close'].iloc[i]
              cumulative_decline = 0.0

      if not np.isnan(threshold) and cumulative_decline <= threshold:
          self.data.at[self.data.index[i], 'Significant'] = 'Yes'
      else:
          self.data.at[self.data.index[i], 'Significant'] = 'No'

      self.data.at[self.data.index[i], 'Cumulative_Decline'] = cumulative_decline

      return peak_index, peak_value, cumulative_decline, consecutive_above_peak

  def load_and_process_data(self, ema_period=20, std_multiplier=2.0):
      """Load the data and process it to calculate the Cumulative Decline with a dynamic threshold."""
      self.load_data()
      self.process_data(ema_period, std_multiplier)

      peak_index = self.data.index[0]
      peak_value = self.data['Close'].iloc[0]
      cumulative_decline = 0.0
      consecutive_above_peak = 0

      for i in range(1, len(self.data)):
          peak_index, peak_value, cumulative_decline, consecutive_above_peak = self.update_peak_and_decline(
              i, peak_index, peak_value, cumulative_decline, consecutive_above_peak, std_multiplier
          )

  def analyze_downturn(self, peak_index, new_peak_index):
      """Analyze the downturn period before a new peak is established."""
      downturn_period = self.data.loc[peak_index:new_peak_index]
      max_drawdown = self.calculate_max_drawdown(downturn_period)
      avg_daily_decline, median_daily_decline, max_daily_decline = self.calculate_percentage_decline_per_day(downturn_period)
      self.decline_stats.append({
          'Peak_Date': peak_index,
          'New_Peak_Date': new_peak_index,
          'Max_Drawdown': max_drawdown,
          'Avg_Daily_Decline': avg_daily_decline,
          'Median_Daily_Decline': median_daily_decline,
          'Max_Daily_Decline': max_daily_decline
      })

  def calculate_max_drawdown(self, downturn_period):
      """Calculate the Maximum Drawdown for a given downturn period."""
      peak = downturn_period['Close'].max()
      trough = downturn_period['Close'].min()
      return (trough - peak) / peak * 100

  def calculate_percentage_decline_per_day(self, downturn_period):
      """Calculate the average, median, and maximum daily percentage decline for a given downturn period."""
      avg_daily_decline = downturn_period['Pct_Change'].mean()
      median_daily_decline = downturn_period['Pct_Change'].median()
      max_daily_decline = downturn_period['Pct_Change'].min()  # Min because declines are negative
      return avg_daily_decline, median_daily_decline, max_daily_decline

  def get_decline_statistics(self):
      """Return a summary of the decline statistics."""
      return self.decline_stats

  def save_data(self):
      """Save the data DataFrame and decline statistics to CSV files."""
      self.data.to_csv('../Down side test/data.csv')
      # self.decline_stats.to_csv('../Down side test/stats.csv', index=False)

# Example Usage
# Create an instance of the analyzer with the file path
analyzer = NiftyDeclineAnalyzer('../Down side test/Nifty 50 Historical Data.csv')

# Load and process the data
analyzer.load_and_process_data()

# Calculate decline statistics
# analyzer.calculate_decline_statistics()

# # Retrieve and print the statistics
# stats_df = analyzer.get_decline_statistics()
# print(stats_df)

# Optionally, save the full data with cumulative declines
analyzer.save_data()