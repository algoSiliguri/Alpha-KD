def calculate_kelly_fraction(
    p: float,
    b: float,
    f_s: float = 0.5,
    clip_negative: bool = True,
) -> float:
    """Calculate fractional Kelly sizing.

    f* = f_s * (p - (1 - p) / b)
    """
    if b <= 0:
        return 0.0
    f_star = f_s * (p - (1.0 - p) / b)
    if clip_negative and f_star < 0:
        return 0.0
    return f_star
