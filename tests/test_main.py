import subprocess
import sys


def test_cli_backtest_flag_runs():
    result = subprocess.run(
        [sys.executable, "-m", "alpha_kd", "--backtest"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr[-500:]}"
    assert "bars" in result.stdout.lower()
