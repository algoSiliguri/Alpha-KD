import numpy as np
import pandas as pd


class MetricsDisplay:
    def __init__(self, data):
        self.data = data

    def display_metrics(self):
        # Average trade duration
        days, hours_left, minutes_left = self.calculate_average_trade_duration()

        # Buy&Sell count
        buy_count, sell_count = self.calculate_buy_sell_count()

        # Return over period
        return_over_period = self.calculate_return_over_period()

        # Calculate drawdown max
        dd_max = self.calculate_drawdown_max()

        # HIT ratio
        hit = self.calculate_hit_ratio()

        # Risk reward ratio
        rr_ratio = self.calculate_risk_reward_ratio()

        # Monthly returns metrics
        pct_winning_month, best_month_return, worse_month_return, cmgr = self.calculate_monthly_returns_metrics()

        # Sharpe Ratio
        sharpe_ratio = self.calculate_sharpe_ratio()

        # Maximum Winning and Losing Streaks
        max_winning_streak, max_losing_streak = self.calculate_streaks(self.data['returns'])

        # Time to Recovery
        time_to_recovery = self.calculate_time_to_recovery(self.data["drawdown"])

        print(
            "------------------------------------------------------------------------------------------------------------------")
        print(
            f" AVERAGE TRADE LIFETIME: {days}D  {hours_left}H  {minutes_left}M \t Nb BUY: {buy_count} \t Nb SELL: {sell_count} ")
        print(
            "                                                                                                                  ")
        print(f" Return (period): {'%.2f' % return_over_period}% \t\t\t\t Maximum drawdown: {'%.2f' % dd_max}%")
        print(f" HIT ratio: {'%.2f' % hit}% \t\t\t\t\t\t R ratio: {'%.2f' % rr_ratio}")
        print(
            f" Best month return: {'%.2f' % best_month_return}% \t\t\t\t Worse month return: {'%.2f' % worse_month_return}%")
        print(f" Average ret/month: {'%.2f' % cmgr}% \t\t\t\t Profitable months: {'%.2f' % pct_winning_month}%")
        print(f" Sharpe Ratio: {'%.2f' % sharpe_ratio}")
        print(f" Max Winning Streak: {max_winning_streak} days \t\t\t Max Losing Streak: {max_losing_streak} days")
        print(f" Time to Recovery: {time_to_recovery} days")
        print(
            "------------------------------------------------------------------------------------------------------------------")

    def calculate_average_trade_duration(self):
        try:
            seconds = self.data.loc[self.data["duration"] != 0]["duration"].mean()
            minutes = seconds // 60
            minutes_left = int(minutes % 60)
            hours = minutes // 60
            hours_left = int(hours % 24)
            days = int(hours / 24)
        except:
            minutes_left = 0
            hours_left = 0
            days = 0
        return days, hours_left, minutes_left

    def calculate_buy_sell_count(self):
        buy_count = self.data["buy_count"].sum()
        sell_count = self.data["sell_count"].sum()
        return buy_count, sell_count

    def calculate_return_over_period(self):
        return self.data["cumulative_returns"].iloc[-1] * 100

    def calculate_drawdown_max(self):
        return -self.data["drawdown"].min() * 100

    def calculate_hit_ratio(self):
        nb_trade_positive = len(self.data.loc[self.data["returns"] > 0])
        nb_trade_negative = len(self.data.loc[self.data["returns"] < 0])
        return nb_trade_positive * 100 / (nb_trade_positive + nb_trade_negative)

    def calculate_risk_reward_ratio(self):
        average_winning_value = self.data.loc[self.data["returns"] > 0]["returns"].mean()
        average_losing_value = self.data.loc[self.data["returns"] < 0]["returns"].mean()
        return -average_winning_value / average_losing_value

    def calculate_monthly_returns_metrics(self):
        months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        years = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]

        ben_month = []

        for month in months:
            for year in years:
                try:
                    information = self.data.loc[f"{year}-{month}"]
                    cum = information["returns"].sum()
                    ben_month.append(cum)
                except:
                    pass

        sr = pd.Series(ben_month, name="returns")

        pct_winning_month = (1 - (len(sr[sr <= 0]) / len(sr))) * 100
        best_month_return = np.max(ben_month) * 100
        worse_month_return = np.min(ben_month) * 100
        cmgr = np.mean(ben_month) * 100

        return pct_winning_month, best_month_return, worse_month_return, cmgr

    def calculate_sharpe_ratio(self):
        risk_free_rate = 0.0706  # Example risk-free rate
        annualized_return = np.prod(1 + self.data["returns"]) ** (252 / len(self.data["returns"])) - 1
        annualized_volatility = np.std(self.data["returns"]) * np.sqrt(252)
        return (annualized_return - risk_free_rate) / annualized_volatility

    @staticmethod
    def calculate_streaks(returns):
        max_winning_streak = 0
        max_losing_streak = 0
        current_winning_streak = 0
        current_losing_streak = 0

        for return_value in returns:
            if return_value > 0:
                current_winning_streak += 1
                current_losing_streak = 0
            elif return_value < 0:
                current_losing_streak += 1
                current_winning_streak = 0
            else:
                current_winning_streak = 0
                current_losing_streak = 0

            if current_winning_streak > max_winning_streak:
                max_winning_streak = current_winning_streak
            if current_losing_streak > max_losing_streak:
                max_losing_streak = current_losing_streak

        return max_winning_streak, max_losing_streak

    @staticmethod
    def calculate_time_to_recovery(drawdown):
        recovery_time = 0
        max_recovery_time = 0
        in_drawdown = False

        for i in range(1, len(drawdown)):
            if drawdown[i] < 0:
                if not in_drawdown:
                    in_drawdown = True
                    recovery_time = 0
                recovery_time += 1
            else:
                if in_drawdown:
                    in_drawdown = False
                    if recovery_time > max_recovery_time:
                        max_recovery_time = recovery_time

        return max_recovery_time

    def get_ret_dd(self):
        return_over_period = self.data["cumulative_returns"].iloc[-1] * 100
        dd_max = self.data["drawdown"].min() * 100
        return return_over_period,dd_max