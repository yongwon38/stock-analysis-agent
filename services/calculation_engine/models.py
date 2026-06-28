from datetime import date
from typing import Optional

from pydantic import BaseModel

from services.data_gateway.models import DataProvenance


class DuPont3Factor(BaseModel):
    net_margin: Optional[float] = None
    asset_turnover: Optional[float] = None
    equity_multiplier: Optional[float] = None
    roe_computed: Optional[float] = None


class FinancialRatios(BaseModel):
    ticker: str
    as_of_date: date
    # Valuation
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    peg_ratio: Optional[float] = None
    # Profitability
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    # Liquidity
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    # Leverage
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    net_debt_to_ebitda: Optional[float] = None
    net_debt: Optional[float] = None
    # Growth (YoY)
    revenue_growth_yoy: Optional[float] = None
    operating_income_growth_yoy: Optional[float] = None
    net_income_growth_yoy: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    fcf_growth_yoy: Optional[float] = None
    # CAGRs (3-year)
    revenue_cagr_3y: Optional[float] = None
    eps_cagr_3y: Optional[float] = None
    # Efficiency
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    days_sales_outstanding: Optional[float] = None
    days_inventory_outstanding: Optional[float] = None
    # DuPont
    dupont_3factor: Optional[DuPont3Factor] = None
    provenance: DataProvenance


class TechnicalIndicators(BaseModel):
    ticker: str
    as_of_date: date
    close: float
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    volume_ratio_20d: Optional[float] = None
    price_vs_52w_high: Optional[float] = None
    price_vs_52w_low: Optional[float] = None
    provenance: DataProvenance
