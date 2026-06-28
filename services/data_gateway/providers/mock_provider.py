"""Mock data provider — returns hardcoded financial data for any ticker.

No network calls; no API keys required.
Suitable for local development and tests.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from services.data_gateway.base import BaseDataProvider
from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DataProvenance,
    IncomeStatement,
    StockPrice,
)

_US_PROFILES = {
    "AAPL": ("Apple Inc.", "Technology", "Consumer Electronics", 2_700_000_000_000.0, 15_550_000_000.0),
    "MSFT": ("Microsoft Corporation", "Technology", "Software", 3_100_000_000_000.0, 7_430_000_000.0),
    "GOOGL": ("Alphabet Inc.", "Communication Services", "Internet Content", 2_000_000_000_000.0, 12_840_000_000.0),
}
_KR_PROFILES = {
    "005930": ("삼성전자", "Technology", "Semiconductors", 350_000_000_000_000.0, 5_969_782_550.0),
    "000660": ("SK하이닉스", "Technology", "Semiconductors", 90_000_000_000_000.0, 728_002_365.0),
    "035420": ("NAVER", "Communication Services", "Internet", 30_000_000_000_000.0, 164_263_395.0),
}

_US_BASE = {
    "revenue": 380_000_000_000.0,
    "cogs_ratio": 0.42,
    "op_margin": 0.30,
    "net_margin": 0.25,
    "total_assets": 350_000_000_000.0,
    "current_assets": 140_000_000_000.0,
    "cash": 60_000_000_000.0,
    "ar": 30_000_000_000.0,
    "inventory": 7_000_000_000.0,
    "current_liabilities": 120_000_000_000.0,
    "long_term_debt": 90_000_000_000.0,
    "short_term_debt": 20_000_000_000.0,
    "total_equity": 60_000_000_000.0,
    "ocf": 110_000_000_000.0,
    "capex": -11_000_000_000.0,
    "close_price": 170.0,
    "growth_rate": 0.10,
    "shares": 15_550_000_000.0,
    "currency": "USD",
    "exchange": "NASDAQ",
}
_KR_BASE = {
    "revenue": 280_000_000_000_000.0,
    "cogs_ratio": 0.55,
    "op_margin": 0.15,
    "net_margin": 0.12,
    "total_assets": 426_000_000_000_000.0,
    "current_assets": 200_000_000_000_000.0,
    "cash": 97_000_000_000_000.0,
    "ar": 40_000_000_000_000.0,
    "inventory": 32_000_000_000_000.0,
    "current_liabilities": 80_000_000_000_000.0,
    "long_term_debt": 10_000_000_000_000.0,
    "short_term_debt": 5_000_000_000_000.0,
    "total_equity": 310_000_000_000_000.0,
    "ocf": 45_000_000_000_000.0,
    "capex": -20_000_000_000_000.0,
    "close_price": 58_700.0,
    "growth_rate": 0.08,
    "shares": 5_969_782_550.0,
    "currency": "KRW",
    "exchange": "KRX",
}


def _prov(today: date | None = None) -> DataProvenance:
    d = today or date.today()
    return DataProvenance(source="mock", as_of_date=d, fetched_at=datetime.now(tz=timezone.utc))


def _base(market: Literal["KR", "US"]) -> dict:
    return dict(_KR_BASE if market == "KR" else _US_BASE)


class MockProvider(BaseDataProvider):
    """Returns deterministic synthetic financial data — no I/O."""

    @property
    def source_name(self) -> str:
        return "mock"

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        b = _base(market)
        if market == "US":
            name, sector, industry, mc, shares = _US_PROFILES.get(
                ticker.upper(), (f"{ticker} Corp.", "Unknown", "Unknown", 100_000_000_000.0, 1_000_000_000.0)
            )
        else:
            name, sector, industry, mc, shares = _KR_PROFILES.get(
                ticker, (f"기업 {ticker}", "Unknown", "Unknown", 10_000_000_000_000.0, 200_000_000.0)
            )
        return CompanyProfile(
            ticker=ticker,
            market=market,
            name=name,
            sector=sector,
            industry=industry,
            market_cap=mc,
            shares_outstanding=shares,
            exchange=b["exchange"],
            currency=b["currency"],
            description=f"[Mock] {name}",
            provenance=_prov(),
        )

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        b = _base(market)
        base_price: float = b["close_price"]
        delta = end_date - start_date
        days = min(delta.days, 365)
        prices = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            if d.weekday() >= 5:  # skip weekends
                continue
            close = round(base_price * (1 + 0.0003 * i), 2)
            prices.append(
                StockPrice(
                    ticker=ticker,
                    market=market,
                    date=d,
                    open=round(close * 0.998, 2),
                    high=round(close * 1.005, 2),
                    low=round(close * 0.993, 2),
                    close=close,
                    adjusted_close=close,
                    volume=10_000_000,
                    provenance=_prov(d),
                )
            )
        return prices

    def get_income_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[IncomeStatement]:
        b = _base(market)
        stmts = []
        today = date.today()
        g = b["growth_rate"]
        for i in range(limit - 1, -1, -1):
            year_offset = limit - 1 - i
            rev = b["revenue"] * ((1 + g) ** year_offset)
            cogs = rev * b["cogs_ratio"]
            gp = rev - cogs
            op_inc = rev * b["op_margin"]
            net_inc = rev * b["net_margin"]
            ebitda = op_inc * 1.12
            shares = b["shares"]
            fiscal_year = today.year - i
            period_end = date(fiscal_year, 12, 31)
            stmts.append(
                IncomeStatement(
                    ticker=ticker,
                    fiscal_year=fiscal_year,
                    period_type=period_type,
                    period_end_date=period_end,
                    revenue=round(rev, 0),
                    cost_of_revenue=round(cogs, 0),
                    gross_profit=round(gp, 0),
                    operating_income=round(op_inc, 0),
                    ebitda=round(ebitda, 0),
                    interest_expense=round(rev * 0.003, 0),
                    pretax_income=round(net_inc * 1.25, 0),
                    income_tax=round(net_inc * 0.25, 0),
                    net_income=round(net_inc, 0),
                    eps_basic=round(net_inc / shares, 4),
                    eps_diluted=round(net_inc / shares, 4),
                    shares_basic=shares,
                    shares_diluted=shares,
                    provenance=_prov(period_end),
                )
            )
        return stmts

    def get_balance_sheets(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[BalanceSheet]:
        b = _base(market)
        sheets = []
        today = date.today()
        g = b["growth_rate"]
        for i in range(limit - 1, -1, -1):
            year_offset = limit - 1 - i
            scale = (1 + g) ** year_offset
            fiscal_year = today.year - i
            period_end = date(fiscal_year, 12, 31)
            sheets.append(
                BalanceSheet(
                    ticker=ticker,
                    period_end_date=period_end,
                    period_type=period_type,
                    total_assets=round(b["total_assets"] * scale, 0),
                    current_assets=round(b["current_assets"] * scale, 0),
                    cash_and_equivalents=round(b["cash"] * scale, 0),
                    accounts_receivable=round(b["ar"] * scale, 0),
                    inventory=round(b["inventory"] * scale, 0),
                    non_current_assets=round((b["total_assets"] - b["current_assets"]) * scale, 0),
                    total_liabilities=round((b["total_assets"] - b["total_equity"]) * scale, 0),
                    current_liabilities=round(b["current_liabilities"] * scale, 0),
                    short_term_debt=round(b["short_term_debt"] * scale, 0),
                    accounts_payable=round(b["current_liabilities"] * 0.3 * scale, 0),
                    long_term_debt=round(b["long_term_debt"] * scale, 0),
                    total_equity=round(b["total_equity"] * scale, 0),
                    retained_earnings=round(b["total_equity"] * 0.8 * scale, 0),
                    provenance=_prov(period_end),
                )
            )
        return sheets

    def get_cash_flow_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[CashFlowStatement]:
        b = _base(market)
        stmts = []
        today = date.today()
        g = b["growth_rate"]
        for i in range(limit - 1, -1, -1):
            year_offset = limit - 1 - i
            scale = (1 + g) ** year_offset
            fiscal_year = today.year - i
            period_end = date(fiscal_year, 12, 31)
            ocf = round(b["ocf"] * scale, 0)
            capex = round(b["capex"] * scale, 0)
            stmts.append(
                CashFlowStatement(
                    ticker=ticker,
                    fiscal_year=fiscal_year,
                    period_type=period_type,
                    period_end_date=period_end,
                    operating_cash_flow=ocf,
                    capex=capex,
                    investing_cash_flow=round(capex * 1.3, 0),
                    financing_cash_flow=round(-ocf * 0.5, 0),
                    dividends_paid=round(-ocf * 0.15, 0),
                    stock_repurchases=round(-ocf * 0.35, 0),
                    provenance=_prov(period_end),
                )
            )
        return stmts
