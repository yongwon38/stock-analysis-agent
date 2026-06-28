from typing import Optional


def yoy_growth(current: float, prior: float) -> Optional[float]:
    if not prior:
        return None
    return (current - prior) / abs(prior)


def cagr(start_value: float, end_value: float, years: float) -> Optional[float]:
    if not start_value or years <= 0:
        return None
    if start_value < 0 or end_value < 0:
        return None
    return (end_value / start_value) ** (1.0 / years) - 1.0


def compute_yoy(values: list[float]) -> Optional[float]:
    """YoY growth from the last two entries in a sorted (oldest→newest) list."""
    if len(values) < 2:
        return None
    return yoy_growth(values[-1], values[-2])


def compute_cagr(values: list[float], years: Optional[int] = None) -> Optional[float]:
    """CAGR from the first and last entries in a sorted (oldest→newest) list."""
    if len(values) < 2:
        return None
    n = years if years is not None else len(values) - 1
    return cagr(values[0], values[-1], float(n))
