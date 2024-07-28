import pandas as pd
import numpy as np
from Quantreo.DataPreprocessing import *


class CciStrategy:
    def __init__(self, data, parameters):
        """
        Initialize the CciStrategy with data and parameters.

        :param data: DataFrame containing the market data.
        :param parameters: Dictionary containing strategy parameters.
        """
        # Set parameters
        self.data = data
        self.cci_period = parameters["cci_period"]
        self.atr_period = parameters["atr_period"]
        self.atr_multiplier = parameters["atr_multiplier"]
        self.cost = parameters["cost"]
        self.start_date_backtest = self.data.index[0]

        # Initialize strategy state variables
        self.buy = False
        self.open_buy_price = None
        self.entry_time = None
        self.exit_time = None  # Added exit_time initialization
        self.trailing_stop = None

        # Initialize output dictionary
        self.output_dictionary = parameters.copy()

        # Calculate features
        self.get_features()

    def get_features(self):
        """
        Calculate the CCI and ATR indicators.
        """
        # Calculate CCI using the cci function
        self.data = cci(self.data, window=self.cci_period)
        # Calculate ATR using the atr function
        self.data = atr(self.data, window=self.atr_period)

    def get_entry_signal(self, time):
        """
        Entry signal
        :param time: TimeStamp of the row
        :return: Entry signal of the row and entry time
        """
        # If there are fewer than 2 rows, we do nothing
        if len(self.data.loc[:time]) < 2:
            return 0, self.entry_time

        # Create entry signal --> 0 or 1
        entry_signal = 0
        cci_current = self.data.loc[time][f"CCI_{self.cci_period}"]
        cci_previous = self.data.loc[:time][f"CCI_{self.cci_period}"][-2]

        # Check if CCI was below -100 and then crosses above -100
        if cci_previous < -100 and cci_current > -100:
            entry_signal = 1

        # Enter in buy position only if we want to, and we aren't already
        if entry_signal == 1 and not self.buy:
            self.buy = True
            self.open_buy_price = self.data.loc[time]["open"]
            self.entry_time = time
            # Initialize the trailing stop
            self.trailing_stop = (
                self.open_buy_price
                - self.atr_multiplier * self.data.loc[time][f"ATR_{self.atr_period}"]
            )
        else:
            entry_signal = 0

        return entry_signal, self.entry_time

    def get_exit_signal(self, time):
        """
        Determine the exit signal based on the ATR trailing stop.

        :param time: TimeStamp of the row.
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
                exit_price - self.open_buy_price - self.cost
            ) / self.open_buy_price
            return profit_loss, self.exit_time

        # If no exit, return 0 and the current exit time
        return 0, self.exit_time
