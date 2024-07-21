import numpy as np
from tqdm import tqdm
import pandas as pd


def find_timestamp_extremum(df, df_lower_timeframe):
    """
    Find the timestamps of the lowest and highest values within each period of a higher timeframe DataFrame.

    :param df: DataFrame of the higher timeframe
    :param df_lower_timeframe: DataFrame of the lower timeframe
    :return: DataFrame with two new columns: low_time (Timestamp), high_time (Timestamp)
    """
    # Create a copy of the higher timeframe DataFrame to avoid modifying the original
    df = df.copy()

    # Ensure the lower timeframe DataFrame covers the period of the higher timeframe DataFrame
    df = df.loc[df_lower_timeframe.index[0] :]

    # Set new columns with default values
    default_time = pd.Timestamp("1970-01-01")
    df["low_time"] = default_time
    df["high_time"] = default_time

    # Loop through each period in the higher timeframe DataFrame
    for i in tqdm(range(len(df) - 1)):
        # Define the start and end of the current period
        start = df.index[i]
        end = df.index[i + 1]

        # Extract the relevant slice from the lower timeframe DataFrame
        row_lowest_timeframe = df_lower_timeframe.loc[start:end].iloc[:-1]

        # Extract the timestamps of the max and min values over the period
        try:
            high = row_lowest_timeframe["high"].idxmax()
            low = row_lowest_timeframe["low"].idxmin()

            df.at[start, "low_time"] = low
            df.at[start, "high_time"] = high

        except Exception as e:
            print(f"Error processing slice from {start} to {end}: {e}")
            df.at[start, "low_time"] = default_time
            df.at[start, "high_time"] = default_time

    # Calculate the percentage of rows with valid low_time and high_time
    valid_rows = df[
        (df["low_time"] != default_time) & (df["high_time"] != default_time)
    ]
    percentage_good_row = len(valid_rows) / len(df) * 100
    percentage_garbage_row = 100 - percentage_good_row

    print(f"WARNINGS: Garbage row: {'%.2f' % percentage_garbage_row} %")

    # Remove the last row as it may not have a complete period
    df = df.iloc[:-1]

    return df


# Example usage
# df_low_tf = pd.read_csv(
#   "../Upstox_Data/Fixed_Time_Bars/AdaniPorts Daily.csv", index_col="time", parse_dates=True
# )
# df_high_tf = pd.read_csv(
#   "../Upstox_Data/Fixed_Time_Bars/AdaniPorts Weekly.csv", index_col="time", parse_dates=True
# )
#
# df = find_timestamp_extremum(df_high_tf, df_low_tf)
#
# # Filter the DataFrame to exclude rows where 'low_time' is '00:00:00'
# default_time = pd.Timestamp('1970-01-01')
# filtered_df = df[df['high_time'] != default_time]
#
# #
# # # Save the filtered DataFrame to a CSV file
# filtered_df.to_csv("FixTimeBars/ADANI_ready.csv")
