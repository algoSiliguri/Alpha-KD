import os

import pandas as pd


class MetricsUtility:
    """
        A utility class to manage and analyze trading metrics for backtesting.

        Attributes:
            loss_trades (list): List of loss trades in terms of capital changes.
            win_trades (list): List of win trades in terms of capital changes.
            capital (float): The initial capital for trading.
            capital_history (list): History of capital over time.
            avg_win (float): Average amount of win per trade.
            avg_loss (float): Average amount of loss per trade.
            win_prob (float): Probability of winning a trade.
            stock_data (list): List of dictionaries containing trade data and metrics.
    """

    def __init__(self):
        self.loss_trades = []
        self.win_trades = []
        self.capital = 0
        self.capital_history = []
        self.avg_win = 0
        self.avg_loss = 0
        self.win_prob = 0
        self.stock_data = []

    def set_capital(self, capital):
        self.capital = capital

    def set_capital_history(self, new_capital):
        self.capital_history.append(new_capital)

    def get_capital_history(self):
        return self.capital_history

    def get_last_capital(self):
        return self.capital_history[-1]

    def calculate_avg_win_loss(self):
        self.win_trades = []
        self.loss_trades = []
        for capital in range(1, len(self.capital_history)):
            diff = self.capital_history[capital] - self.capital_history[capital - 1]
            if diff > 0:
                self.win_trades.append(diff)
            else:
                self.loss_trades.append(diff)

        self.avg_win = sum(self.win_trades) / len(self.win_trades) if self.win_trades else 0
        self.avg_loss = sum(self.loss_trades) / len(self.loss_trades) if self.loss_trades else 0

    def calculate_winprob(self):
        total_trades = len(self.win_trades) + len(self.loss_trades)
        self.win_prob = len(self.win_trades) / total_trades if total_trades > 0 else 0

    def recalculate_capital(self, trade_return):
        new_capital = (1 + trade_return) * self.capital_history[-1]
        self.capital_history.append(new_capital)

    def construct_stock_data(self, trade_return, entry_trade_time, exit_trade_time):
        self.calculate_avg_win_loss()  # Recalculate averages after this trade
        self.calculate_winprob()  # Recalculate win probability after this trade
        self.stock_data.append({
            'entry_trade_time': pd.Timestamp(entry_trade_time).strftime('%Y-%m-%d %H:%M:%S'),
            'last_capital': self.capital_history[-3] if len(self.capital_history) > 2 else self.capital,
            'profit/loss': trade_return,
            'win_prob': self.win_prob,
            'new_capital': self.get_last_capital(),
            'exit_trade_time': pd.Timestamp(exit_trade_time).strftime('%Y-%m-%d %H:%M:%S')
        })

    def save_to_csv(self, stock_name):
        df = pd.DataFrame(self.stock_data)
        file_path = os.path.join('Backtest_Data', 'Daily', f'{stock_name}.csv')
        df.to_csv(file_path, index=False)
