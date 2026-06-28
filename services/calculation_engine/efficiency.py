from typing import Optional


def asset_turnover(revenue: float, avg_assets: Optional[float]) -> Optional[float]:
    if not avg_assets:
        return None
    return revenue / avg_assets


def inventory_turnover(
    cost_of_revenue: float,
    avg_inventory: Optional[float],
) -> Optional[float]:
    if not avg_inventory:
        return None
    return cost_of_revenue / avg_inventory


def receivables_turnover(revenue: float, avg_ar: Optional[float]) -> Optional[float]:
    if not avg_ar:
        return None
    return revenue / avg_ar


def days_sales_outstanding(recv_turnover: Optional[float]) -> Optional[float]:
    if not recv_turnover:
        return None
    return 365.0 / recv_turnover


def days_inventory_outstanding(inv_turnover: Optional[float]) -> Optional[float]:
    if not inv_turnover:
        return None
    return 365.0 / inv_turnover


def days_payable_outstanding(
    cost_of_revenue: float,
    avg_ap: Optional[float],
) -> Optional[float]:
    if not avg_ap or not cost_of_revenue:
        return None
    return (avg_ap / cost_of_revenue) * 365.0
