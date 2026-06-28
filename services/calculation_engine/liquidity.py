from typing import Optional


def current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
    if not current_liabilities:
        return None
    return current_assets / current_liabilities


def quick_ratio(
    current_assets: float,
    inventory: Optional[float],
    current_liabilities: float,
) -> Optional[float]:
    if not current_liabilities:
        return None
    inv = inventory or 0.0
    return (current_assets - inv) / current_liabilities


def cash_ratio(cash: float, current_liabilities: float) -> Optional[float]:
    if not current_liabilities:
        return None
    return cash / current_liabilities
