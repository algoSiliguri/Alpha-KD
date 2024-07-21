import pandas as pd
from Quantreo.Backtest import Backtest
from datetime import timedelta
import random
import statistics
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm


class MonteCarlo:
    def __init__(
        self,
        data,
        TradingStrategy,
        parameters,
        raw_columns=[],
        discount_calmar_ratio=252,
    ):
        self.data = data
        self.TradingStrategy = TradingStrategy
        self.parameters = parameters
        self.raw_columns = raw_columns
        self.discount_calmar_ratio = discount_calmar_ratio
        self.paths = []
        self.returns, self.drawdowns = [], []

    @staticmethod
    def compute_historical_variations(df):
        """
        Compute percentage variations between open and other prices (low, high, close).

        Parameters:
        df (pd.DataFrame): DataFrame containing stock price data with columns 'open', 'low', 'high', 'close'.

        Returns:
        pd.DataFrame: DataFrame with additional columns for percentage variations.
        """
        df["pct_open_low"] = (df["low"] - df["open"]) / df["open"]
        df["pct_open_high"] = (df["high"] - df["open"]) / df["open"]
        df["pct_open_close"] = (df["close"] - df["open"]) / df["open"]
        return df

    @staticmethod
    def infer_data_frequency(df):
        """
        Infer the frequency of the data based on the datetime index.

        Parameters:
        df (pd.DataFrame): DataFrame with a datetime index.

        Returns:
        str: Inferred frequency of the data.

        Raises:
        ValueError: If the frequency cannot be inferred.
        """
        freq = pd.infer_freq(df.index.date)
        if freq is None:
            raise ValueError(
                "Cannot infer frequency of the data. Ensure the index is a datetime index with a regular frequency."
            )
        return freq

    @staticmethod
    def compute_time_variations(df, freq):
        """
        Compute time variations based on the inferred frequency.

        Parameters:
        df (pd.DataFrame): DataFrame with a datetime index.
        freq (str): Inferred frequency of the data.

        Returns:
        pd.DataFrame: DataFrame with an additional column for time variations.
        """
        if freq.startswith("D"):
            # 6.5 hours in seconds for a trading day
            time_index = [23400] * len(df)
        elif freq.startswith("W"):
            # 5 trading days in a week
            time_index = [23400 * 5] * len(df)
        elif freq.startswith("M"):
            # 21 trading days in a month
            time_index = [23400 * 21] * len(df)
        else:
            # For intraday data, compute the actual time differences
            time_index = list((df.index[1:] - df.index[:-1]).total_seconds())
            mode = statistics.multimode(time_index)
            time_index.insert(0, mode[0])

        df["time_variation"] = time_index
        return df

    def generate_synthetic_data(self, df, number_observation):
        """
        Generate synthetic data based on historical variations and time variations.

        Parameters:
        df (pd.DataFrame): DataFrame with historical variations and time variations.
        number_observation (int): Number of synthetic observations to generate.

        Returns:
        pd.DataFrame: DataFrame with synthetic data.
        """
        data = []
        for i in range(len(df)):
            row_values = [
                df["pct_open_low"].iloc[i],
                df["pct_open_high"].iloc[i],
                df["pct_open_close"].iloc[i],
                df["time_variation"].iloc[i],
                df["var_low_time"].iloc[i],
                df["var_high_time"].iloc[i],
            ]
            for col in self.raw_columns:
                row_values.append(df[col].iloc[i])
            data.append(row_values)

        start_price, start_date = df["open"].iloc[-1], df.index[-1]
        open_price, current_date = start_price, start_date
        data_new = []

        for _ in range(number_observation):
            row_values = random.choice(data)
            pct_open_low, pct_open_high, pct_open_close = (
                row_values[0],
                row_values[1],
                row_values[2],
            )
            time_variation, var_low_time, var_high_time = (
                row_values[3],
                row_values[4],
                row_values[5],
            )
            raw_data = [row_values[6 + i] for i in range(len(self.raw_columns))]

            current_date += timedelta(seconds=int(time_variation))
            low_time = current_date + timedelta(seconds=int(var_low_time))
            high_time = current_date + timedelta(seconds=int(var_high_time))

            low_price = open_price * (1 + pct_open_low)
            high_price = open_price * (1 + pct_open_high)
            close_price = open_price * (1 + pct_open_close)

            if close_price < low_price:
                low_price = close_price
            if high_price < close_price:
                high_price = close_price

            row_data_new = [
                open_price,
                low_price,
                high_price,
                close_price,
                current_date,
                low_time,
                high_time,
            ]
            row_data_new.extend(raw_data)
            data_new.append(row_data_new)
            open_price = close_price

        columns_list = ["open", "low", "high", "close", "time", "low_time", "high_time"]
        columns_list.extend(self.raw_columns)
        df_simulated = pd.DataFrame(data_new, columns=columns_list)
        df_simulated = df_simulated.set_index("time")
        return df_simulated

    def generate_path(self, number_observation=1000):
        """
        Generate a synthetic path of stock prices.

        Parameters:
        number_observation (int): Number of synthetic observations to generate.

        Returns:
        pd.DataFrame: DataFrame with synthetic stock price data.
        """
        df = self.data.copy()
        df = self.compute_historical_variations(df)
        freq = self.infer_data_frequency(df)
        df = self.compute_time_variations(df, freq)
        df["var_low_time"] = (pd.to_datetime(df["low_time"]) - df.index).map(
            lambda x: x.total_seconds()
        )
        df["var_high_time"] = (pd.to_datetime(df["high_time"]) - df.index).map(
            lambda x: x.total_seconds()
        )
        return self.generate_synthetic_data(df, number_observation)

    def generate_paths(self, number_simulations=100, number_observation=1000):
        """
        Generate multiple simulated paths and store them in self.paths.

        Parameters:
        number_simulations (int): Number of simulation paths to generate.
        number_observation (int): Number of observations in each simulation path.
        """
        for _ in range(number_simulations):
            df_sim = self.generate_path(number_observation=number_observation)
            self.paths.append(df_sim)

    def backtest_paths(self):
        """
        Backtest each generated path using the specified trading strategy.
        If no paths are generated, it will generate them first.
        """
        if len(self.paths) == 0:
            self.generate_paths()

        for df_path in tqdm(self.paths, desc="Backtesting paths"):
            BT = Backtest(
                data=df_path,
                TradingStrategy=self.TradingStrategy,
                parameters=self.parameters,
            )
            BT.run()
            ret, dd = BT.get_ret_dd()
            self.returns.append(ret)
            self.drawdowns.append(dd)

    def display_results(self):
        """
        Display the results of the backtests including return distribution,
        drawdown distribution, and Calmar ratio distribution.
        If no backtests have been run, it will run them first.
        """
        if len(self.returns) == 0:
            self.backtest_paths()

        # Calculate Calmar ratio for each path
        ret_dd = [
            return_ / np.abs(dd) / (len(self.paths[0]) / self.discount_calmar_ratio)
            for return_, dd in zip(self.returns, self.drawdowns)
        ]

        # Create subplots for the distributions
        fig, axs = plt.subplots(3, 1, figsize=(15, 10))

        # Plot return distribution
        axs[0].hist(
            self.returns, color="#289E41", bins=40, alpha=0.7, edgecolor="black"
        )
        axs[0].set_title("Return Distribution %")
        axs[0].grid(axis="y", linestyle="-", alpha=0.5, color="lightgrey")

        # Plot drawdown distribution
        axs[1].hist(
            self.drawdowns, color="#9E2828", bins=40, alpha=0.7, edgecolor="black"
        )
        axs[1].set_title("Drawdown Distribution %")
        axs[1].grid(axis="y", linestyle="-", alpha=0.5, color="lightgrey")

        # Plot Calmar ratio distribution
        axs[2].hist(ret_dd, color="#28709E", bins=40, alpha=0.7, edgecolor="black")
        axs[2].set_title("Calmar Ratio Distribution")
        axs[2].grid(axis="y", linestyle="-", alpha=0.5, color="lightgrey")

        # Adjust layout and show plot
        plt.subplots_adjust(hspace=0.5)
        plt.show()

