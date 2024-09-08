import pandas as pd
import numpy as np
from Quantreo.DataPreprocessing import *
from Quantreo.MetricsUtility import MetricsUtility


class CciStrategy:
    def __init__(self, data, parameters, metricUtility):
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
        self.metricUtility = metricUtility

        # Initialize strategy state variables
        self.buy = False
        self.open_buy_price = None
        self.entry_time = None
        self.exit_time = None  # Added exit_time initialization
        self.trailing_stop = None
        self.shares = 0  # Added shares
        self.max_capital_used = 0  # Added max_capital used

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

    def calculate_max_shares_and_capital(self, open_price, available_capital):  # Added max_shares_and_capital function
        """
        Calculate the maximum number of shares that can be bought and the capital used.

        :param open_price: The price at which shares are bought.
        :return: Tuple of maximum shares and capital used.
        """
        if open_price <= 0:
            raise ValueError("Open price must be greater than zero.")
        max_shares = available_capital // open_price
        max_capital_used = max_shares * open_price
        return int(max_shares), max_capital_used

    def get_entry_signal(self, time):
        """
        Entry signal
        :param time: TimeStamp of the row
        :return: Entry signal of the row and entry time
        """
        # If we are in the first or second columns, we do nothing
        if len(self.data.loc[:time]) < 2:
            return 0, self.entry_time

        # Create entry signal --> 0 or 1
        entry_signal = 0
        cci_current = self.data.loc[time][f"CCI_{self.cci_period}"]
        cci_previous = self.data.loc[:time][f"CCI_{self.cci_period}"][-2]

        # Check if CCI was below -100 and then crosses above -100
        if cci_previous < -100 < cci_current:
            entry_signal = 1

        # Enter in buy position only if we want to, and we aren't already
        if entry_signal == 1 and not self.buy:
            self.buy = True
            self.open_buy_price = self.data.loc[time]["open"]
            self.entry_time = time

            # Get the last available capital from the history
            available_capital = self.metricUtility.get_last_capital()
            # Calculate the maximum number of shares and capital used
            self.shares, self.max_capital_used = self.calculate_max_shares_and_capital(self.open_buy_price,
                                                                                       available_capital)

            if self.shares <= 0:  # Not enough capital to buy even 1 share
                self.buy = False
                return 0, self.entry_time

            updated_capital = available_capital - self.max_capital_used

            self.metricUtility.set_capital_history(updated_capital)

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
            exit_price = self.data.loc[time]["open"]  # Assuming we exit at the next open price
            # Calculate profit/loss
            profit_loss = ((exit_price - self.open_buy_price) * self.shares - self.cost) / self.max_capital_used
            # Get the last available capital before the exit
            available_capital = self.metricUtility.get_last_capital()
            # Update the capital with profit or loss from the trade
            updated_capital = available_capital + self.max_capital_used * (1 + profit_loss)

            # Insert the updated capital back into the capital history
            self.metricUtility.set_capital_history(updated_capital)

            # Reset shares and other position variables after the trade is closed
            self.shares = 0
            self.open_buy_price = None
            self.trailing_stop = None

            return profit_loss, self.exit_time

        # If no exit, return 0 and the current exit time
        return 0, self.exit_time
