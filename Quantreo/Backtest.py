import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

from Quantreo.MetricsDisplay import MetricsDisplay
from Strategies.CciStrategy import CciStrategy
from Strategies.DpoStrategy import DpoStrategy
from Strategies.DoubleEmaStrategy import DoubleEmaStrategy


class Backtest:
    """
  A class for backtesting trading strategies.

  This class is used to execute a backtest of a given trading strategy on historical data. It allows
  to compute various trading metrics such as cumulative returns, drawdown, and other statistics. It
  can also visualize the backtest results.

  Parameters
  ----------
  data : DataFrame
      The historical data to backtest the trading strategy on. The DataFrame should be indexed by time
      and contain at least the price data.

  TradingStrategy : object
      The trading strategy to be backtested. This should be an instance of a class that implements
      a `get_entry_signal` and `get_exit_signal` methods.

  parameters : dict
      The parameters of the strategy that should be used during the backtest.

  run_directly : bool, default False
      If True, the backtest is executed upon initialization. Otherwise, the `run` method should be
      called explicitly.

  title : str, default None
      The title of the backtest's plot. If None, a default title will be used.
  """

    def __init__(self, data, TradingStrategy, parameters, run_directly=False, title=None):
        self.TradingStrategy = TradingStrategy(data, parameters)
        self.start_date_backtest = self.TradingStrategy.start_date_backtest
        self.data = data.loc[self.start_date_backtest:].copy()

        if "returns" not in self.data.columns:
            self.data["returns"] = 0
        if "duration" not in self.data.columns:
            self.data["duration"] = 0
        if "buy_count" not in self.data.columns:
            self.data["buy_count"] = 0
        if "sell_count" not in self.data.columns:
            self.data["sell_count"] = 0

        self.count_buy, self.count_sell = 0, 0
        self.entry_trade_time, self.exit_trade_time = None, None

        # Initialize MetricsDisplay with the data
        self.metrics_display = MetricsDisplay(self.data)

        if run_directly:
            self.run()
            self.get_vector_metrics()
            self.metrics_display = MetricsDisplay(self.data)
            self.metrics_display.display_metrics()
            self.display_graphs(title)

    def run(self) -> None:
        for current_time in tqdm(self.data.index, desc="Running Backtest"):
            # Maybe open a position
            entry_signal, self.entry_trade_time = self.TradingStrategy.get_entry_signal(
                current_time
            )
            self.data.loc[current_time, "buy_count"] = 1 if entry_signal == 1 else 0
            self.data.loc[current_time, "sell_count"] = 1 if entry_signal == -1 else 0

            # Maybe close a position
            position_return, self.exit_trade_time = (
                self.TradingStrategy.get_exit_signal(current_time)
            )

            # Store position return and duration when we close a trade
            if position_return != 0:
                self.data.loc[current_time, "returns"] = position_return
                self.data.loc[current_time, "duration"] = (
                    self.exit_trade_time - self.entry_trade_time
                ).total_seconds()
    def get_vector_metrics(self):
        # Compute Cumulative Returns
        self.data["cumulative_returns"] = self.data["returns"].cumsum()

        # We compute max of the cumsum on the period (accumulate max) # (1,3,5,3,1) --> (1,3,5,5,5) - 0.01 --> 1.01
        running_max = np.maximum.accumulate(self.data["cumulative_returns"] + 1)

        # We compute drawdown
        self.data["drawdown"] = (self.data["cumulative_returns"] + 1) / running_max - 1

    def display_graphs(self, title=None):

        # Compute the cumulative returns and the drawdown
        self.get_vector_metrics()

        # Take cum returns and drawdown of the strategy
        cum_ret = self.data["cumulative_returns"]
        drawdown = self.data["drawdown"]

        # Set font style
        plt.rc('font', weight='bold', size=12)

        # Put a subplots
        fig, (cum, dra) = plt.subplots(2, 1, figsize=(15, 7))
        plt.setp(cum.spines.values(), color="#ffffff")
        plt.setp(dra.spines.values(), color="#ffffff")

        # Change suptitle if we put one in the input or put the title by default
        if title is None:
            fig.suptitle("Overview of the Strategy", size=18, fontweight='bold')
        else:
            fig.suptitle(title, size=18, fontweight='bold')

        # Returns cumsum chart
        cum.plot(cum_ret * 100, color="#569878", linewidth=1.5)
        cum.fill_between(cum_ret.index, cum_ret * 100, 0,
                         cum_ret >= 0, color="#569878", alpha=0.30)
        cum.axhline(0, color="#569878")
        cum.grid(axis="y", color='#505050', linestyle='--', linewidth=1, alpha=0.5)
        cum.set_ylabel("Cumulative Return (%)", size=15, fontweight='bold')

        # Put the drawdown
        dra.plot(drawdown.index, drawdown * 100, color="#C04E4E", alpha=0.50, linewidth=0.5)
        dra.fill_between(drawdown.index, drawdown * 100, 0,
                         drawdown * 100 <= 0, color="#C04E4E", alpha=0.30)
        dra.grid(axis="y", color='#505050', linestyle='--', linewidth=1, alpha=0.5)
        dra.set_ylabel("Drawdown (%)", size=15, fontweight='bold')

        # Plot the graph
        plt.show()


# Load data
data = pd.read_csv('../Upstox_Data/Create_Database/Nifty50_data/Daily/ADANIENT_Daily.csv', index_col="time",
                   parse_dates=True)

# Filter data to include only the most recent two years
recent_two_years = data.loc[data.index >= (data.index.max() - pd.DateOffset(years=2))].copy()

# Define strategy parameters
parameters = {
    "cci_period": 20,  # Example value, adjust as needed
    "atr_period": 14,  # Example value, adjust as needed
    "atr_multiplier": 1.5,  # Example value, adjust as needed
    "cost": 10
}

# Initialize and run the backtest
backtest = Backtest(recent_two_years, CciStrategy, parameters, run_directly=True, title="Cci Strategy Backtest")
