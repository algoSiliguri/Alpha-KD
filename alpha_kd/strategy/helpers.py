import pandas as pd
import ta


def _sma(df: pd.DataFrame, col: str, n: int) -> pd.DataFrame:
    df[f"SMA_{n}"] = ta.trend.SMAIndicator(df[col], int(n)).sma_indicator()
    return df


def _rsi(df: pd.DataFrame, col: str, n: int) -> pd.DataFrame:
    df = df.copy()
    df["RSI"] = ta.momentum.RSIIndicator(df[col], int(n)).rsi()
    return df


def check_buy_exit(row, open_price, tp, sl, cost, leverage):
    var_high = (row["high"] - open_price) / open_price
    var_low = (row["low"] - open_price) / open_price
    if tp < var_high and var_low < sl:
        if row["high_time"] < row["low_time"]:
            return True, (tp - cost) * leverage, var_high, var_low
        if row["low_time"] < row["high_time"]:
            return True, (sl - cost) * leverage, var_high, var_low
        return True, 0.0, var_high, var_low
    if tp < var_high:
        return True, (tp - cost) * leverage, var_high, var_low
    if var_low < sl:
        return True, (sl - cost) * leverage, var_high, var_low
    return False, 0.0, var_high, var_low


def check_sell_exit(row, open_price, tp, sl, cost, leverage):
    var_high = -(row["high"] - open_price) / open_price
    var_low = -(row["low"] - open_price) / open_price
    if tp < var_low and var_high < sl:
        if row["low_time"] < row["high_time"]:
            return True, (tp - cost) * leverage, var_high, var_low
        if row["high_time"] < row["low_time"]:
            return True, (sl - cost) * leverage, var_high, var_low
        return True, 0.0, var_high, var_low
    if tp < var_low:
        return True, (tp - cost) * leverage, var_high, var_low
    if var_high < sl:
        return True, (sl - cost) * leverage, var_high, var_low
    return False, 0.0, var_high, var_low
