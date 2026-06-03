"""Tests for multi-ticker portfolio replay and drawdown breaker integration."""
import json
import pandas as pd
from alpha_kd.telemetry.backtest import BacktestTelemetry
from alpha_kd.strategy.base import Strategy


class DummyStrategy(Strategy):
    """A dummy strategy that exits with configured returns on specific times."""

    def get_features(self) -> None:
        pass

    def get_entry_signal(self, time: pd.Timestamp):
        if not self.buy:
            self.buy = True
            self.open_buy_price = 100.0
            return 1, time
        return 0, None

    def get_exit_signal(self, time: pd.Timestamp):
        ret = self.data.loc[time, "exit_ret"]
        if ret != 0.0:
            self.buy = False
            self.open_buy_price = None
            return ret, time
        return 0.0, None

    def get_state(self, time=None):
        state = super().get_state(time)
        state["unrealized_pnl"] = 0.0
        return state


def test_multi_ticker_alignment_and_drawdown(tmp_path):
    idx1 = pd.to_datetime([
        "2026-06-01 10:00:00",
        "2026-06-01 11:00:00",
        "2026-06-01 12:00:00"
    ])
    idx2 = pd.to_datetime([
        "2026-06-01 10:30:00",
        "2026-06-01 11:00:00",
        "2026-06-01 13:00:00"
    ])

    df1 = pd.DataFrame(
        {"open": [100, 100, 100], "exit_ret": [0.0, -0.25, 0.0]},
        index=idx1
    )
    df2 = pd.DataFrame(
        {"open": [100, 100, 100], "exit_ret": [0.0, 0.0, 0.0]},
        index=idx2
    )

    data = {"T1": df1, "T2": df2}
    telemetry_file = tmp_path / "test_telemetry.jsonl"

    bt = BacktestTelemetry(
        data=data,
        TradingStrategy=DummyStrategy,
        parameters={},
        initial_capital=100000.0,
        telemetry_path=telemetry_file,
    )

    expected_timeline = sorted(list(set(idx1).union(set(idx2))))
    assert bt.timeline == expected_timeline

    bt.run()

    records = []
    with open(telemetry_file, "r") as f:
        for line in f:
            records.append(json.loads(line))

    assert len(records) == len(expected_timeline)
    assert not records[0]["is_halted"]
    assert records[0]["equity"] == 100000.0

    # The sorted timeline is:
    # 0: 10:00:00
    # 1: 10:30:00
    # 2: 11:00:00  <-- T1 loses 25% (exit_ret=-0.25), triggering drawdown breaker
    # 3: 12:00:00  <-- halted
    # 4: 13:00:00  <-- halted
    assert records[2]["is_halted"]
    assert records[3]["is_halted"]
    assert records[4]["is_halted"]
    assert records[2]["equity"] == 87500.0
