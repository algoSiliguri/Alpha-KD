import numpy as np
import pandas as pd


class MetricsDisplay:
    def __init__(self, data):
        self.data = data

    def display_metrics(self) -> None:

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
