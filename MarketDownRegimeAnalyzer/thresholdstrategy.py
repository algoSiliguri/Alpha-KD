import pandas as pd
import numpy as np
from Quantreo.DataPreprocessing import *


class CustomStrategy:
    def __init__(self, data, parameters):
        """
        Initialize the CustomStrategy with data and parameters.

        :param data: DataFrame containing the market data.
        :param parameters: Dictionary containing strategy parameters.
        """
        # Set parameters
        self.data = data
        self.atr_period = parameters["atr_period"]
        self.atr_multiplier = parameters["atr_multiplier"]
        self.cost = parameters["cost"]
        self.start_date_backtest = self.data.index[0]

        # Initialize strategy state variables
        self.buy = False
        self.open_buy_price = None
        self.entry_time = None
        self.exit_time = None
        self.trailing_stop = None
        self.shares = 0  # Initialize the number of shares

        # Initialize output dictionary
        self.output_dictionary = parameters.copy()

        # Calculate features
        self.get_features()

    def get_features(self):
        """
        Calculate the ATR indicator.
        """
        # Calculate ATR using the atr function
        self.data = atr(self.data, window=self.atr_period)

    def get_entry_signal(self, time):
        """
        Determine the entry signal based on specific conditions.

        :param time: Timestamp of the row.
        :return: Tuple containing the entry signal (0 or 1) and entry time.
        """
        # If we are in the first or second columns, we do nothing
        if len(self.data.loc[:time]) < 2:
            return 0, self.entry_time

        # Create entry signal --> 0 or 1
        entry_signal = 0
        current_row = self.data.loc[time]
        previous_row = self.data.loc[:time].iloc[-2]

        # Check the conditions for the buy signal
        if (
            current_row["Significant"] == "Yes"
            and previous_row["Significant"] == "Yes"
            and current_row["Threshold"] > previous_row["Threshold"]
            and current_row["Cumulative_Decline"]
            < previous_row["Cumulative_Decline"] - 0.1
        ):
            entry_signal = 1

        # Enter in buy position or add to existing position
        if entry_signal == 1:
            current_price = self.data.loc[time]["open"]
            if not self.buy:
                self.buy = True
                self.open_buy_price = current_price
                self.entry_time = time
                self.shares = 1  # Initial buy of 1 share
                # Initialize the trailing stop
                self.trailing_stop = (
                    self.open_buy_price
                    - self.atr_multiplier
                    * self.data.loc[time][f"ATR_{self.atr_period}"]
                )
            else:
                # Calculate the new average price
                self.open_buy_price = (
                    (self.open_buy_price * self.shares) + current_price
                ) / (self.shares + 1)
                self.shares += 1  # Add another share to the existing position

        return entry_signal, self.entry_time

    def get_exit_signal(self, time):
        """
        Determine the exit signal based on the ATR trailing stop.

        :param time: Timestamp of the row.
        :return: Tuple containing the profit/loss of the row and exit time.
        """
        # Check if there is an active buy position
        if not self.buy:
            return 0, self.exit_time

        # Ensure the time exists in the data
        if time not in self.data.index:
            raise ValueError(f"Time {time} not found in data")

        # Update the trailing stop
        current_price = self.data.loc[time]["close"]
        current_atr = self.data.loc[time][f"ATR_{self.atr_period}"]
        new_trailing_stop = current_price - self.atr_multiplier * current_atr

        # Adjust the trailing stop only if it moves up
        if new_trailing_stop > self.trailing_stop:
            self.trailing_stop = new_trailing_stop

        # Exit the position if the price falls below the trailing stop
        if current_price < self.trailing_stop:
            self.buy = False
            self.exit_time = time
            exit_price = self.data.loc[time][
                "open"
            ]  # Assuming we exit at the next open price
            profit_loss = (
                (exit_price - self.open_buy_price - self.cost) * self.shares
            ) / self.open_buy_price
            self.shares = 0  # Reset the number of shares after exit
            return profit_loss, self.exit_time

        # If no exit, return 0 and the current exit time
        return 0, self.exit_time
