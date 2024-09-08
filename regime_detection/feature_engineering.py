import numpy as np
import pandas as pd


class FeatureEngineering:
    @staticmethod
    def calculate_log_return_of_moving_average(df, window=7):
        """
        Calculate the log return of the moving average of historical close prices and drop NaN values.

        Parameters:
        df (pd.DataFrame): DataFrame containing the historical data with a 'close' column.
        window (int): The window size for the moving average. Default is 7.

        Returns:
        pd.DataFrame: A pandas DataFrame containing the log returns of the moving average with NaN values dropped.

        Raises:
        KeyError: If the 'close' column is not present in the DataFrame.
        ValueError: If the DataFrame is empty or if the window size is inappropriate.
        """
        try:
            # Check if 'close' column exists
            if "close" not in df.columns:
                raise KeyError("The DataFrame must contain a 'close' column.")

            # Calculate the moving average of the 'close' prices
            df["moving_avg"] = df["close"].rolling(window=window).mean()

            # Calculate the log returns of the moving average
            df["log_return"] = np.log(df["moving_avg"] / df["moving_avg"].shift(1))

            # Drop NaN values
            df.dropna(inplace=True)

            return df

        except KeyError as e:
            print(f"KeyError: {e}")
            raise
        except ValueError as e:
            print(f"ValueError: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

    @staticmethod
    def normalize_data(df, column_name):
        """
        Normalize the specified column in the DataFrame to have zero mean and unit variance.

        Parameters:
        df (pd.DataFrame): DataFrame containing the data to be normalized.
        column_name (str): The name of the column to normalize.

        Returns:
        pd.DataFrame: A pandas DataFrame with the specified column normalized.

        Raises:
        KeyError: If the specified column is not present in the DataFrame.
        ValueError: If the DataFrame is empty or if the column has zero variance.
        """
        try:
            # Check if the specified column exists
            if column_name not in df.columns:
                raise KeyError(f"The DataFrame must contain a '{column_name}' column.")

            mean = df[column_name].mean()
            std = df[column_name].std()

            # Check for zero variance
            if std == 0:
                raise ValueError(f"The column '{column_name}' has zero variance.")

            df[column_name] = (df[column_name] - mean) / std
            return df

        except KeyError as e:
            print(f"KeyError: {e}")
            raise
        except ValueError as e:
            print(f"ValueError: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
