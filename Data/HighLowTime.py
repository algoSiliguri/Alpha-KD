import numpy as np
from tqdm import tqdm
import pandas as pd

def find_timestamp_extremum(df, df_lower_timeframe):
  """
  :param df: DataFrame of the higher timeframe
  :param df_lower_timeframe: DataFrame of the lower timeframe
  :return: DataFrame with three new columns: low_time (Timestamp), high_time (Timestamp)
  """
  df = df.copy()
  df = df.loc[df_lower_timeframe.index[0]:]

  # Set new columns with default values
  default_time = pd.Timestamp('1970-01-01')
  df["low_time"] = default_time
  df["high_time"] = default_time

  # Loop to find out which of the high or low appears first
  for i in tqdm(range(len(df) - 1)):
      # Extract values from the lowest timeframe dataframe
      start = df.iloc[i:i + 1].index[0]
      end = df.iloc[i + 1:i + 2].index[0]
      row_lowest_timeframe = df_lower_timeframe.loc[start:end].iloc[:-1]

      # Extract Timestamp of the max and min over the period (highest timeframe)
      try:
          high = row_lowest_timeframe["high"].idxmax()
          low = row_lowest_timeframe["low"].idxmin()

          df.loc[start, "low_time"] = low
          df.loc[start, "high_time"] = high

      except Exception as e:
          print(f"Error processing slice from {start} to {end}: {e}")
          df.loc[start, "low_time"] = default_time
          df.loc[start, "high_time"] = default_time

  # Verify the number of rows without both TP and SL on the same time
  percentage_good_row = len(df[(df["low_time"] != default_time) & (df["high_time"] != default_time)]) / len(df) * 100
  percentage_garbage_row = 100 - percentage_good_row

  print(f"WARNINGS: Garbage row: {'%.2f' % percentage_garbage_row} %")

  df = df.iloc[:-1]

  return df

# Example usage
df_low_tf = pd.read_csv(
  "../Upstox_Data/Fixed_Time_Bars/AdaniPorts Daily.csv", index_col="time", parse_dates=True
)
df_high_tf = pd.read_csv(
  "../Upstox_Data/Fixed_Time_Bars/AdaniPorts Weekly.csv", index_col="time", parse_dates=True
)

df = find_timestamp_extremum(df_high_tf, df_low_tf)

# Filter the DataFrame to exclude rows where 'low_time' is '00:00:00'
default_time = pd.Timestamp('1970-01-01')
filtered_df = df[df['high_time'] != default_time]

#
# # Save the filtered DataFrame to a CSV file
filtered_df.to_csv("FixTimeBars/ADANI_ready.csv")