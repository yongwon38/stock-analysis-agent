from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DataProvenance(BaseModel):
    source: str
    as_of_date: date
    fetched_at: datetime

    @field_validator("source")
    @classmethod
    def source_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("DataProvenance.source must not be empty")
        return v


class StockPrice(BaseModel):
    ticker: str
    market: Literal["KR", "US"]
    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: Optional[float] = None
    volume: int
    provenance: DataProvenance


class CompanyProfile(BaseModel):
    ticker: str
    market: Literal["KR", "US"]
    name: str
    name_en: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    shares_outstanding: Optional[float] = None
    description: Optional[str] = None
    exchange: str
    currency: str
    dart_corp_code: Optional[str] = None
    provenance: DataProvenance


class IncomeStatement(BaseModel):
    ticker: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    period_type: Literal["annual", "quarterly"]
    period_end_date: date
    revenue: float
    cost_of_revenue: float
    gross_profit: float
    operating_income: float
    ebitda: Optional[float] = None
    interest_expense: Optional[float] = None
    pretax_income: float
    income_tax: Optional[float] = None
    net_income: float
    eps_basic: Optional[float] = None
    eps_diluted: Optional[float] = None
    shares_basic: float
    shares_diluted: Optional[float] = None
    provenance: DataProvenance


class BalanceSheet(BaseModel):
    ticker: str
    period_end_date: date
    period_type: Literal["annual", "quarterly"]
    total_assets: float
    current_assets: float
    cash_and_equivalents: float
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    non_current_assets: Optional[float] = None
    total_liabilities: float
    current_liabilities: float
    short_term_debt: Optional[float] = None
    accounts_payable: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_equity: float
    retained_earnings: Optional[float] = None
    provenance: DataProvenance

    @model_validator(mode="after")
    def _total_debt(self) -> "BalanceSheet":
        # Expose a convenient computed property-like field
        return self

    @property
    def total_debt(self) -> float:
        return (self.short_term_debt or 0.0) + (self.long_term_debt or 0.0)


class CashFlowStatement(BaseModel):
    ticker: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    period_type: Literal["annual", "quarterly"]
    period_end_date: date
    operating_cash_flow: float
    capex: float
    free_cash_flow: float = Field(description="Always computed: OCF - abs(capex)")
    investing_cash_flow: float
    financing_cash_flow: float
    dividends_paid: Optional[float] = None
    stock_repurchases: Optional[float] = None
    provenance: DataProvenance

    @model_validator(mode="before")
    @classmethod
    def _compute_fcf(cls, values: dict) -> dict:
        if "free_cash_flow" not in values or values.get("free_cash_flow") is None:
            ocf = values.get("operating_cash_flow", 0.0) or 0.0
            capex = values.get("capex", 0.0) or 0.0
            values["free_cash_flow"] = ocf - abs(capex)
        return values


class DARTFiling(BaseModel):
    corp_code: str
    ticker: str
    report_name: str
    receipt_no: str
    filed_at: date
    url: str
    summary: Optional[str] = None
    provenance: DataProvenance
