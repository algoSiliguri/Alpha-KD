import pandas as pd
import ta


class TradingStrategy:
    def __init__(self, data):
        """
        Initialize the TradingStrategy with data.

        :param data: DataFrame containing intraday data with columns: Datetime, Open, High, Low, Close, Volume
        """
        self.data = data
        self.calculate_vwap()
        # Implement correct logic for gap determination
        self.data["Gap"] = (
            (self.data["Open"] - self.data["Close"].shift(1))
            / self.data["Close"].shift(1)
            * 100
        )

    def calculate_vwap(self):
        """
        Calculate VWAP and add it to the DataFrame.
        """
        self.data["VWAP"] = ta.volume.volume_weighted_average_price(
            self.data["High"], self.data["Low"], self.data["Close"], self.data["Volume"]
        )

    def check_gap_up(self, i):
        """
        Check for gap up conditions and return buy signal if conditions are met.

        :param i: Current index in the DataFrame
        :return: Boolean indicating whether to buy
        """
        if self.data["Gap"].iloc[i] > 3:
            if i >= 60 and self.data["Close"].iloc[i] >= self.data["Close"].iloc[60]:
                if (
                    i >= 120
                    and self.data["Close"].iloc[i] >= self.data["Close"].iloc[120]
                ):
                    if self.data["Close"].iloc[i] >= self.data["VWAP"].iloc[i]:
                        return True
        return False

    def check_flat_open(self, i):
        """
        Check for flat open conditions and return buy signal if conditions are met.

        :param i: Current index in the DataFrame
        :return: Boolean indicating whether to buy
        """
        if -1 <= self.data["Gap"].iloc[i] <= 1:
            if self.data["Close"].iloc[i] >= self.data["VWAP"].iloc[i]:
                return True
        return False

    def check_gap_down(self, i):
        """
        Check for gap down conditions and return buy signal if conditions are met.

        :param i: Current index in the DataFrame
        :return: Boolean indicating whether to buy
        """
        if self.data["Gap"].iloc[i] < -3:
            if self.data["Close"].iloc[i] >= self.data["VWAP"].iloc[i]:
                return True
        return False

    def create_signals(self, symbol, timeframe):
        """
        Create buy and sell signals based on the strategy logic.

        :param symbol: Trading symbol
        :param timeframe: Timeframe for trading signals
        :return: Tuple of buy and sell signals (buy, sell)
        """
        buy = False
        sell = False

        for i in range(len(self.data)):
            # Skip the first 30 minutes and last 15 minutes of the market session
            current_time = self.data["Datetime"].iloc[i].time()
            if (
                current_time < pd.Timestamp("09:45").time()
                or current_time > pd.Timestamp("15:00").time()
            ):
                continue

            if (
                self.check_gap_up(i)
                or self.check_flat_open(i)
                or self.check_gap_down(i)
            ):
                buy = True
                break  # Exit loop after the first buy signal

        return buy, sell


# Example usage
# Load your intraday data into a DataFrame
# df = pd.read_csv('your_intraday_data.csv', parse_dates=['Datetime'])

# Initialize the strategy
# strategy = TradingStrategy(df)

# Apply the strategy
# buy, sell = strategy.create_signals('AAPL', '1min')

# Print the signals
# print(f"Buy: {buy}, Sell: {sell}")
