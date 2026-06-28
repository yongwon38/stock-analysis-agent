from typing import Optional


def debt_to_equity(total_debt: float, total_equity: float) -> Optional[float]:
    if not total_equity:
        return None
    return total_debt / total_equity


def debt_to_assets(total_debt: float, total_assets: float) -> Optional[float]:
    if not total_assets:
        return None
    return total_debt / total_assets


def interest_coverage(ebit: float, interest_expense: Optional[float]) -> Optional[float]:
    if not interest_expense:
        return None
    return ebit / interest_expense


def net_debt(total_debt: float, cash: float) -> float:
    return total_debt - cash


def net_debt_to_ebitda(
    total_debt: float,
    cash: float,
    ebitda: Optional[float],
) -> Optional[float]:
    if not ebitda or ebitda <= 0:
        return None
    nd = net_debt(total_debt, cash)
    return nd / ebitda
