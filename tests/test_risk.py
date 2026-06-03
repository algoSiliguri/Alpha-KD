from alpha_kd.risk.breaker import DrawdownBreaker
from alpha_kd.risk.kelly import calculate_kelly_fraction


def test_drawdown_breaker_halt():
    breaker = DrawdownBreaker(limit=0.10, initial_value=100.0)
    assert not breaker.is_halted
    assert not breaker.update(95.0)
    assert not breaker.is_halted
    assert not breaker.update(105.0)  # new peak is 105
    assert not breaker.is_halted
    # 105 * 0.9 = 94.5. Let's drop to 94.0.
    assert breaker.update(94.0)
    assert breaker.is_halted
    # Once halted, it stays halted.
    assert breaker.update(200.0)
    assert breaker.is_halted


def test_kelly_fraction():
    # win prob = 0.6, win/loss = 2.0, full Kelly = 0.6 - 0.4 / 2 = 0.4
    # half Kelly (f_s = 0.5) should be 0.2
    f = calculate_kelly_fraction(p=0.6, b=2.0, f_s=0.5)
    assert abs(f - 0.2) < 1e-6

    # negative kelly should clip to 0
    f_neg = calculate_kelly_fraction(p=0.3, b=1.0, f_s=0.5)
    assert f_neg == 0.0

    # negative win/loss ratio should return 0
    assert calculate_kelly_fraction(p=0.5, b=-1.0) == 0.0
