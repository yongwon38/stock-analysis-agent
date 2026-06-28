from typing import Optional


def gross_margin(gross_profit: float, revenue: float) -> Optional[float]:
    if not revenue:
        return None
    return gross_profit / revenue


def operating_margin(operating_income: float, revenue: float) -> Optional[float]:
    if not revenue:
        return None
    return operating_income / revenue


def net_margin(net_income: float, revenue: float) -> Optional[float]:
    if not revenue:
        return None
    return net_income / revenue


def ebitda_margin(ebitda: Optional[float], revenue: float) -> Optional[float]:
    if ebitda is None or not revenue:
        return None
    return ebitda / revenue


def roe(net_income: float, avg_equity: Optional[float]) -> Optional[float]:
    if not avg_equity:
        return None
    return net_income / avg_equity


def roa(net_income: float, avg_assets: Optional[float]) -> Optional[float]:
    if not avg_assets:
        return None
    return net_income / avg_assets


def roic(
    ebit: float,
    tax_rate: float,
    total_debt: float,
    total_equity: float,
    cash: float,
) -> Optional[float]:
    invested_capital = total_equity + total_debt - cash
    if not invested_capital:
        return None
    nopat = ebit * (1.0 - tax_rate)
    return nopat / invested_capital


def avg(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    return (a + b) / 2.0
