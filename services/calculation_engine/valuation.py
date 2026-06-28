from typing import Optional


def pe_ratio(close_price: float, eps_ttm: Optional[float]) -> Optional[float]:
    if not eps_ttm or eps_ttm <= 0:
        return None
    return close_price / eps_ttm


def pb_ratio(close_price: float, book_value_per_share: Optional[float]) -> Optional[float]:
    if not book_value_per_share or book_value_per_share <= 0:
        return None
    return close_price / book_value_per_share


def ps_ratio(close_price: float, revenue_per_share: Optional[float]) -> Optional[float]:
    if not revenue_per_share or revenue_per_share <= 0:
        return None
    return close_price / revenue_per_share


def enterprise_value(
    market_cap: float,
    total_debt: float,
    cash: float,
) -> float:
    return market_cap + total_debt - cash


def ev_ebitda(ev: float, ebitda_ttm: Optional[float]) -> Optional[float]:
    if not ebitda_ttm or ebitda_ttm <= 0:
        return None
    return ev / ebitda_ttm


def ev_revenue(ev: float, revenue_ttm: Optional[float]) -> Optional[float]:
    if not revenue_ttm or revenue_ttm <= 0:
        return None
    return ev / revenue_ttm


def peg_ratio(pe: Optional[float], earnings_growth_rate: Optional[float]) -> Optional[float]:
    """earnings_growth_rate as a decimal (e.g. 0.15 for 15%)."""
    if pe is None or earnings_growth_rate is None or earnings_growth_rate <= 0:
        return None
    return pe / (earnings_growth_rate * 100)
