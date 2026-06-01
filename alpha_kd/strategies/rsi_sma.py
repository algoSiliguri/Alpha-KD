"""
RSI + SMA divergence strategy.

Logic: trade divergence between SMA trend direction and RSI momentum direction.
Buy when SMAs show downtrend but RSI momentum turns up; sell for the inverse.
"""
from typing import Optional, Tuple

import pandas as pd
import ta

from alpha_kd.strategies.base import Strategy


def _sma(df: pd.DataFrame, col: str, n: int) -> pd.DataFrame:
    df[f"SMA_{n}"] = ta.trend.SMAIndicator(df[col], int(n)).sma_indicator()
    return df


def _rsi(df: pd.DataFrame, col: str, n: int) -> pd.DataFrame:
    df = df.copy()
    df["RSI"] = ta.momentum.RSIIndicator(df[col], int(n)).rsi()
    return df


class RsiSma(Strategy):

    def __init__(self, data: pd.DataFrame, parameters: dict):
        self.fast_sma = parameters["fast_sma"]
        self.slow_sma = parameters["slow_sma"]
        self.rsi_period = parameters["rsi"]
        self.tp = parameters["tp"]
        self.sl = parameters["sl"]
        self.cost = parameters["cost"]
        self.leverage = parameters["leverage"]

        self.var_buy_high: Optional[float] = None
        self.var_buy_low: Optional[float] = None
        self.var_sell_high: Optional[float] = None
        self.var_sell_low: Optional[float] = None
        self.output_dictionary = parameters.copy()

        super().__init__(data, parameters)

    def get_features(self) -> None:
        self.data = _sma(self.data, "close", self.fast_sma)
        self.data = _sma(self.data, "close", self.slow_sma)
        self.data = _rsi(self.data, "close", self.rsi_period)

        self.data["signal"] = 0
        self.data["RSI_retarded"] = self.data["RSI"].shift(1)

        condition_1_buy = self.data[f"SMA_{self.fast_sma}"] < self.data[f"SMA_{self.slow_sma}"]
        condition_1_sell = self.data[f"SMA_{self.fast_sma}"] > self.data[f"SMA_{self.slow_sma}"]
        condition_2_buy = self.data["RSI"] > self.data["RSI_retarded"]
        condition_2_sell = self.data["RSI"] < self.data["RSI_retarded"]

        self.data.loc[condition_1_buy & condition_2_buy, "signal"] = 1
        self.data.loc[condition_1_sell & condition_2_sell, "signal"] = -1

    def get_entry_signal(self, time: pd.Timestamp) -> Tuple[int, Optional[pd.Timestamp]]:
        if len(self.data.loc[:time]) < 2:
            return 0, self.entry_time

        entry_signal = 0
        last_signal = self.data.loc[:time]["signal"].iloc[-2]
        if last_signal == 1:
            entry_signal = 1
        elif last_signal == -1:
            entry_signal = -1

        if entry_signal == 1 and not self.buy and not self.sell:
            self.buy = True
            self.open_buy_price = self.data.loc[time]["open"]
            self.entry_time = time
        elif entry_signal == -1 and not self.sell and not self.buy:
            self.sell = True
            self.open_sell_price = self.data.loc[time]["open"]
            self.entry_time = time
        else:
            entry_signal = 0

        return entry_signal, self.entry_time

    def get_exit_signal(self, time: pd.Timestamp) -> Tuple[float, Optional[pd.Timestamp]]:
        row = self.data.loc[time]

        if self.buy:
            self.var_buy_high = (row["high"] - self.open_buy_price) / self.open_buy_price
            self.var_buy_low = (row["low"] - self.open_buy_price) / self.open_buy_price

            if (self.tp < self.var_buy_high) and (self.var_buy_low < self.sl):
                self.buy = False
                self.open_buy_price = None
                self.exit_time = time
                if row["high_time"] < row["low_time"]:
                    return (self.tp - self.cost) * self.leverage, self.exit_time
                elif row["low_time"] < row["high_time"]:
                    return (self.sl - self.cost) * self.leverage, self.exit_time
                return 0.0, self.exit_time

            elif self.tp < self.var_buy_high:
                self.buy = False
                self.open_buy_price = None
                self.exit_time = time
                return (self.tp - self.cost) * self.leverage, self.exit_time

            elif self.var_buy_low < self.sl:
                self.buy = False
                self.open_buy_price = None
                self.exit_time = time
                return (self.sl - self.cost) * self.leverage, self.exit_time

        if self.sell:
            self.var_sell_high = -(row["high"] - self.open_sell_price) / self.open_sell_price
            self.var_sell_low = -(row["low"] - self.open_sell_price) / self.open_sell_price

            if (self.tp < self.var_sell_low) and (self.var_sell_high < self.sl):
                self.sell = False
                self.open_sell_price = None
                self.exit_time = time
                if row["low_time"] < row["high_time"]:
                    return (self.tp - self.cost) * self.leverage, self.exit_time
                elif row["high_time"] < row["low_time"]:
                    return (self.sl - self.cost) * self.leverage, self.exit_time
                return 0.0, self.exit_time

            elif self.tp < self.var_sell_low:
                self.sell = False
                self.open_sell_price = None
                self.exit_time = time
                return (self.tp - self.cost) * self.leverage, self.exit_time

            elif self.var_sell_high < self.sl:
                self.sell = False
                self.open_sell_price = None
                self.exit_time = time
                return (self.sl - self.cost) * self.leverage, self.exit_time

        return 0.0, None
