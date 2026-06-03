from alpha_kd.data.loader import init_horizon_telemetry


def test_init_horizon_telemetry(tmp_path):
    tel_path = tmp_path / "telemetry.jsonl"
    bt = init_horizon_telemetry("Historical Backtest", ["AAPL"], tel_path)
    assert bt is not None
    assert bt.symbols == ["AAPL"]
    assert len(bt.timeline) > 0
