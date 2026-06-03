from typing import Optional, Tuple

import pandas as pd

from alpha_kd.strategy.base import Strategy
from alpha_kd.strategy.helpers import (
    _rsi,
    _sma,
    check_buy_exit,
    check_sell_exit,
)


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

        c1_buy = self.data[f"SMA_{self.fast_sma}"] < self.data[f"SMA_{self.slow_sma}"]
        c1_sell = self.data[f"SMA_{self.fast_sma}"] > self.data[f"SMA_{self.slow_sma}"]
        c2_buy = self.data["RSI"] > self.data["RSI_retarded"]
        c2_sell = self.data["RSI"] < self.data["RSI_retarded"]

        self.data.loc[c1_buy & c2_buy, "signal"] = 1
        self.data.loc[c1_sell & c2_sell, "signal"] = -1

    def get_entry_signal(
        self, time: pd.Timestamp
    ) -> Tuple[int, Optional[pd.Timestamp]]:
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

    def get_exit_signal(
        self, time: pd.Timestamp
    ) -> Tuple[float, Optional[pd.Timestamp]]:
        row = self.data.loc[time]

        if self.buy and self.open_buy_price is not None:
            is_exit, ret, vh, vl = check_buy_exit(
                row, self.open_buy_price, self.tp, self.sl, self.cost, self.leverage
            )
            self.var_buy_high = vh
            self.var_buy_low = vl
            if is_exit:
                self.buy = False
                self.open_buy_price = None
                self.exit_time = time
                return ret, self.exit_time

        if self.sell and self.open_sell_price is not None:
            is_exit, ret, vh, vl = check_sell_exit(
                row, self.open_sell_price, self.tp, self.sl, self.cost, self.leverage
            )
            self.var_sell_high = vh
            self.var_sell_low = vl
            if is_exit:
                self.sell = False
                self.open_sell_price = None
                self.exit_time = time
                return ret, self.exit_time

        return 0.0, None

    def get_state(self, time=None) -> dict:
        state = super().get_state(time)
        last_close = self.data.loc[time if (time is not None and time in self.data.index) else self.data.index[-1], "close"]
        if self.buy and self.open_buy_price:
            state["unrealized_pnl"] = (
                (last_close - self.open_buy_price) / self.open_buy_price
            )
            state["signal"] = 1
        elif self.sell and self.open_sell_price:
            state["unrealized_pnl"] = (
                (self.open_sell_price - last_close) / self.open_sell_price
            )
            state["signal"] = -1
        state["timestamp"] = str(time if (time is not None and time in self.data.index) else self.data.index[-1])
        return state
