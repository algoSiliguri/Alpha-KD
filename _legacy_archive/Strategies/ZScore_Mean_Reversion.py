import pandas as pd

from Quantreo.DataPreprocessing import atr


class MeanReversionStrategy:
    def __init__(self, data, parameters):
        """
        Initialize the MeanReversionStrategy with data and parameters.

        :param data: DataFrame containing the market data.
        :param parameters: Dictionary containing strategy parameters.
        """
        # Set parameters
        self.data = data
        self.zscore_period = parameters["zscore_period"]
        self.zscore_threshold = parameters["zscore_threshold"]
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

        # Initialize output dictionary
        self.output_dictionary = parameters.copy()

        # Calculate features
        self.get_features()

    def get_features(self):
        """
        Calculate the Z-Score and ATR indicators.
        """
        self.data["mean"] = (
            self.data["close"].ewm(span=self.zscore_period, adjust=False).mean()
        )
        self.data["std"] = (
            self.data["close"].ewm(span=self.zscore_period, adjust=False).std()
        )
        self.data["zscore"] = (self.data["close"] - self.data["mean"]) / self.data[
            "std"
        ]
        self.data = atr(self.data, window=self.atr_period)

    def get_entry_signal(self, time):
        """
        Determine the entry signal based on the Z-Score.

        :param time: TimeStamp of the row.
        :return: Tuple containing the entry signal (0 or 1) and entry time.
        """
        # If we are in the first or second columns, we do nothing
        if len(self.data.loc[:time]) < self.zscore_period:
            return 0, self.entry_time

        # Create entry signal --> 0 or 1
        entry_signal = 0
        zscore_current = self.data.loc[time]["zscore"]

        # Check if Z-Score is below the negative threshold
        if zscore_current < -self.zscore_threshold:
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
