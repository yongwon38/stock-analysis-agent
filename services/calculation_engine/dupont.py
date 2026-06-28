from typing import Optional

from services.calculation_engine.models import DuPont3Factor


def dupont_3factor(
    net_margin: Optional[float],
    asset_turnover: Optional[float],
    equity_multiplier: Optional[float],
) -> DuPont3Factor:
    roe_computed: Optional[float] = None
    if all(v is not None for v in [net_margin, asset_turnover, equity_multiplier]):
        roe_computed = net_margin * asset_turnover * equity_multiplier  # type: ignore[operator]
    return DuPont3Factor(
        net_margin=net_margin,
        asset_turnover=asset_turnover,
        equity_multiplier=equity_multiplier,
        roe_computed=roe_computed,
    )


def equity_multiplier(total_assets: float, total_equity: float) -> Optional[float]:
    if not total_equity:
        return None
    return total_assets / total_equity
