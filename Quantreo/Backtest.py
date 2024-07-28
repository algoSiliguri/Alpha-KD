import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import Any, Dict, Optional, Tuple

from Strategies.CciStrategy import CciStrategy


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

    def __init__(
        self,
        data: pd.DataFrame,
        TradingStrategy: Any,
        parameters: Dict[str, Any],
        run_directly: bool = False,
        title: Optional[str] = None,
    ):
        self.TradingStrategy = TradingStrategy(data, parameters)
        self.start_date_backtest = self.TradingStrategy.start_date_backtest
        self.data = data.loc[
            self.start_date_backtest :
        ].copy()  # Use .copy() to avoid SettingWithCopyWarning

        # Initialize columns if they don't exist
        for col in ["returns", "duration", "buy_count", "sell_count"]:
            if col not in self.data.columns:
                self.data[col] = 0

        self.count_buy, self.count_sell = 0, 0
        self.entry_trade_time, self.exit_trade_time = None, None

        if run_directly:
            self.run()
            self.display_metrics()
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

    def get_vector_metrics(self) -> None:
        # Compute Cumulative Returns
        self.data["cumulative_returns"] = self.data["returns"].cumsum()

        # Compute drawdown
        running_max = np.maximum.accumulate(self.data["cumulative_returns"] + 1)
        self.data["drawdown"] = (self.data["cumulative_returns"] + 1) / running_max - 1

    def display_metrics(self) -> None:
        self.get_vector_metrics()

        try:
            seconds = self.data.loc[self.data["duration"] != 0]["duration"].mean()
            if pd.isna(seconds):
                raise ValueError("No trades executed.")
            minutes = seconds // 60
            minutes_left = int(minutes % 60)
            hours = minutes // 60
            hours_left = int(hours % 24)
            days = int(hours / 24)
        except Exception as e:
            print(f"Error calculating average trade lifetime: {e}")
            minutes_left = 0
            hours_left = 0
            days = 0

        buy_count = self.data["buy_count"].sum()
        sell_count = self.data["sell_count"].sum()
        return_over_period = self.data["cumulative_returns"].iloc[-1] * 100
        dd_max = -self.data["drawdown"].min() * 100

        nb_trade_positive = len(self.data.loc[self.data["returns"] > 0])
        nb_trade_negative = len(self.data.loc[self.data["returns"] < 0])
        hit = (
            nb_trade_positive * 100 / (nb_trade_positive + nb_trade_negative)
            if (nb_trade_positive + nb_trade_negative) > 0
            else 0
        )

        average_winning_value = self.data.loc[self.data["returns"] > 0][
            "returns"
        ].mean()
        average_losing_value = self.data.loc[self.data["returns"] < 0]["returns"].mean()
        rr_ratio = (
            -average_winning_value / average_losing_value
            if average_losing_value != 0
            else np.nan
        )

        months = [f"{i:02d}" for i in range(1, 13)]
        years = [
            str(year)
            for year in range(
                self.data.index.year.min(), self.data.index.year.max() + 1
            )
        ]

        ben_month = []
        for month in months:
            for year in years:
                try:
                    information = self.data.loc[f"{year}-{month}"]
                    cum = information["returns"].sum()
                    ben_month.append(cum)
                except KeyError:
                    pass

        sr = pd.Series(ben_month, name="returns")
        pct_winning_month = (
            (1 - (len(sr[sr <= 0]) / len(sr))) * 100 if len(sr) > 0 else 0
        )
        best_month_return = np.max(ben_month) * 100 if ben_month else 0
        worse_month_return = np.min(ben_month) * 100 if ben_month else 0
        cmgr = np.mean(ben_month) * 100 if ben_month else 0

        print(
            "------------------------------------------------------------------------------------------------------------------"
        )
        print(
            f" AVERAGE TRADE LIFETIME: {days}D  {hours_left}H  {minutes_left}M \t Nb BUY: {buy_count} \t Nb SELL: {sell_count} "
        )
        print(
            "                                                                                                                  "
        )
        print(
            f" Return (period): {'%.2f' % return_over_period}% \t\t\t\t Maximum drawdown: {'%.2f' % dd_max}%"
        )
        print(f" HIT ratio: {'%.2f' % hit}% \t\t\t\t\t\t R ratio: {'%.2f' % rr_ratio}")
        print(
            f" Best month return: {'%.2f' % best_month_return}% \t\t\t\t Worse month return: {'%.2f' % worse_month_return}%"
        )
        print(
            f" Average ret/month: {'%.2f' % cmgr}% \t\t\t\t Profitable months: {'%.2f' % pct_winning_month}%"
        )
        print(
            "------------------------------------------------------------------------------------------------------------------"
        )

    def display_graphs(self, title: Optional[str] = None) -> None:
        self.get_vector_metrics()

        cum_ret = self.data["cumulative_returns"]
        drawdown = self.data["drawdown"]

        plt.rc("font", weight="bold", size=12)
        fig, (cum, dra) = plt.subplots(2, 1, figsize=(15, 7))
        plt.setp(cum.spines.values(), color="#ffffff")
        plt.setp(dra.spines.values(), color="#ffffff")

        fig.suptitle(
            title if title else "Overview of the Strategy", size=18, fontweight="bold"
        )

        cum.plot(cum_ret * 100, color="#569878", linewidth=1.5)
        cum.fill_between(
            cum_ret.index, cum_ret * 100, 0, cum_ret >= 0, color="#569878", alpha=0.30
        )
        cum.axhline(0, color="#569878")
        cum.grid(axis="y", color="#505050", linestyle="--", linewidth=1, alpha=0.5)
        cum.set_ylabel("Cumulative Return (%)", size=15, fontweight="bold")

        dra.plot(
            drawdown.index, drawdown * 100, color="#C04E4E", alpha=0.50, linewidth=0.5
        )
        dra.fill_between(
            drawdown.index,
            drawdown * 100,
            0,
            drawdown * 100 <= 0,
            color="#C04E4E",
            alpha=0.30,
        )
        dra.grid(axis="y", color="#505050", linestyle="--", linewidth=1, alpha=0.5)
        dra.set_ylabel("Drawdown (%)", size=15, fontweight="bold")

        plt.show()

    def get_ret_dd(self) -> Tuple[float, float]:
        self.get_vector_metrics()
        return_over_period = self.data["cumulative_returns"].iloc[-1] * 100
        dd_max = self.data["drawdown"].min() * 100
        return return_over_period, dd_max

    def display(self, title: Optional[str] = None) -> None:
        self.display_metrics()
        self.display_graphs(title)


# Example Usage
#
# data = pd.read_csv('../Data/FixTimeBars/ADANI_ready.csv',index_col="time",
#     parse_dates=True,)
#
# # Define strategy parameters
# parameters = {
#     "tp":0.02,
#     "sl": -0.01,
#     "fast_sma": 50,
#     "slow_sma": 20,
#     "rsi": 14,
#     "cost": 0.0001,
#     "leverage": 5
# }
#
# # Initialize and run the backtest
# backtest = Backtest(data, CciStrategy, parameters, run_directly=True, title="Cci Strategy Backtest")


# # Load data
# data = pd.read_csv('../Upstox_Data/Create_Database/Nifty50_data/Daily/ADANIENT_Daily.csv', index_col="time", parse_dates=True)
#
# # Filter data to include only the most recent two years
# recent_two_years = data.loc[data.index >= (data.index.max() - pd.DateOffset(years=2))]
#
# # Define strategy parameters
# parameters = {
#   "cci_period": 20,  # Example value, adjust as needed
#   "atr_period": 14,  # Example value, adjust as needed
#   "atr_multiplier": 1.5,  # Example value, adjust as needed
#   "cost": 10
# }
#
# # Initialize and run the backtest
# backtest = Backtest(data, CciStrategy, parameters, run_directly=True, title="Cci Strategy Backtest")
