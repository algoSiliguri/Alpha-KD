from typing import Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Metrics:
    """
    A class for calculating and displaying various trading metrics based on input data.

    This class processes trading data to compute metrics such as
    Return (period),
    Number of Buys,
    Number of sells,
    Average Trade Lifetime,
    Maximum drawdown,
    Profitable months,
    Best month return,
    Worse month return,
    Average ret/month

    Parameters
    ----------
    data : DataFrame
       The historical data to backtest the trading strategy on. The DataFrame should be indexed by time
       and contain at least the price data.
    """

    def __init__(self, data):
        self.data = data
        self.return_over_period = self.calculate_return_over_period()
        self.buy_count = self.get_buy_count()
        self.sell_count = self.get_sell_count()
        self.days, self.hours_left, self.minutes_left = (
            self.calculate_average_trade_lifetime()
        )
        self.dd_max = self.get_dd_max()
        self.hit = self.calculate_hit()
        self.rr_ratio = self.calculate_rr_ratio()
        self.ben_month = self.calculate_ben_month()
        self.pct_winning_month = self.calculate_pct_winning_month()
        self.best_month_return = self.get_best_month_return()
        self.worse_month_return = self.get_worse_month_return()
        self.cmgr = self.get_cmgr()
        self.max_winning_streak, self.max_losing_streak = Metrics.calculate_streaks(self.data['returns'])
        self.sharpe_ratio = self.calculate_sharpe_ratio()

        self.display_metrics()

    def calculate_return_over_period(self):
        return self.data["cumulative_returns"].iloc[-1] * 100

    def get_buy_count(self):
        return self.data["buy_count"].sum()

    def get_sell_count(self):
        return self.data["sell_count"].sum()

    def calculate_average_trade_lifetime(self):
        try:
            seconds = self.data.loc[self.data["duration"] != 0]["duration"].mean()
            if pd.isna(seconds):
                raise ValueError("No trades executed.")
            minutes = seconds // 60
            minutes_left = int(minutes % 60)
            hours = minutes // 60
            hours_left = int(hours % 24)
            days = int(hours / 24)
            return days, hours_left, minutes_left
        except Exception as e:
            print(f"Error calculating average trade lifetime: {e}")
            minutes_left = 0
            hours_left = 0
            days = 0

    def get_dd_max(self):
        return -self.data["drawdown"].min() * 100

    def calculate_hit(self):
        nb_trade_positive = len(self.data.loc[self.data["returns"] > 0])
        nb_trade_negative = len(self.data.loc[self.data["returns"] < 0])
        return (
            nb_trade_positive * 100 / (nb_trade_positive + nb_trade_negative)
            if (nb_trade_positive + nb_trade_negative) > 0
            else 0
        )

    def calculate_rr_ratio(self):
        average_winning_value = self.data.loc[self.data["returns"] > 0][
            "returns"
        ].mean()
        average_losing_value = self.data.loc[self.data["returns"] < 0]["returns"].mean()
        return (
            -average_winning_value / average_losing_value
            if average_losing_value != 0
            else np.nan
        )

    def calculate_ben_month(self):
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
        return ben_month

    def calculate_pct_winning_month(self):
        sr = pd.Series(self.ben_month, name="returns")
        return (1 - (len(sr[sr <= 0]) / len(sr))) * 100 if len(sr) > 0 else 0

    def calculate_sharpe_ratio(self):
        # Assuming 252 trading days in a year
        trading_days = 252

        # Annual risk-free rate
        annual_risk_free_rate = 0.0706  # Example rate, adjust as needed
        daily_risk_free_rate = (1 + annual_risk_free_rate) ** (1 / trading_days) - 1

        # Calculate daily excess returns
        excess_returns = self.data["returns"] - daily_risk_free_rate

        # Calculate annualized return
        annualized_return = np.mean(self.data["returns"]) * trading_days

        # Calculate annualized standard deviation of excess returns
        annualized_std_excess_return = np.std(excess_returns, ddof=1) * np.sqrt(trading_days)

        # Calculate annualized Sharpe ratio
        sharpe_ratio = (annualized_return - annual_risk_free_rate) / annualized_std_excess_return

        return sharpe_ratio

    @staticmethod
    def calculate_streaks(returns):
        max_winning_streak = 0
        max_losing_streak = 0
        current_winning_streak = 0
        current_losing_streak = 0

        for return_value in returns:
            if return_value > 0:
                current_winning_streak += 1
                if current_winning_streak > max_winning_streak:
                    max_winning_streak = current_winning_streak
                current_losing_streak = 0
            elif return_value < 0:
                current_losing_streak += 1
                if current_losing_streak > max_losing_streak:
                    max_losing_streak = current_losing_streak
                current_winning_streak = 0
            else:
                current_winning_streak = 0
                current_losing_streak = 0

        return max_winning_streak, max_losing_streak

    def get_best_month_return(self):
        return np.max(self.ben_month) * 100 if self.ben_month else 0

    def get_worse_month_return(self):
        return np.min(self.ben_month) * 100 if self.ben_month else 0

    def get_cmgr(self):
        return np.mean(self.ben_month) * 100 if self.ben_month else 0

    def display_metrics(self) -> None:

        print(
            "------------------------------------------------------------------------------------------------------------------"
        )
        print(
            f" AVERAGE TRADE LIFETIME: {self.days}D  {self.hours_left}H  {self.minutes_left}M \t Nb BUY: {self.buy_count} \t Nb SELL: {self.sell_count}"
        )
        print(
            "                                                                                                                  "
        )
        print(
            f" Return (period): {'%.2f' % self.return_over_period}% \t\t\t\t Maximum drawdown: {'%.2f' % self.dd_max}%"
        )
        print(
            f" HIT ratio: {'%.2f' % self.hit}% \t\t\t\t\t\t R ratio: {'%.2f' % self.rr_ratio}"
        )
        print(
            f" Best month return: {'%.2f' % self.best_month_return}% \t\t\t\t Worse month return: {'%.2f' % self.worse_month_return}%"
        )
        print(
            f" Average ret/month: {'%.2f' % self.cmgr}% \t\t\t\t Profitable months: {'%.2f' % self.pct_winning_month}%"
        )
        print(
            f" Sharpe Ratio: {'%.2f' % self.sharpe_ratio} \t\t\t\t\t Streaks: {self.max_winning_streak, self.max_losing_streak}"
        )
        print(
            "------------------------------------------------------------------------------------------------------------------"
        )
