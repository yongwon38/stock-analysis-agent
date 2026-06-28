"""Financial Modeling Prep provider — US fundamentals."""
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

import httpx

from services.data_gateway.base import BaseDataProvider
from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DataProvenance,
    IncomeStatement,
    StockPrice,
)

_FMP_BASE = "https://financialmodelingprep.com/api/v3"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _prov(as_of: date) -> DataProvenance:
    return DataProvenance(source="fmp", as_of_date=as_of, fetched_at=_now())


def _f(val: Any) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


class FMPProvider(BaseDataProvider):
    """US fundamentals via Financial Modeling Prep API."""

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    @property
    def source_name(self) -> str:
        return "fmp"

    def _get(self, path: str, **params: Any) -> Any:
        params["apikey"] = self._key
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{_FMP_BASE}/{path}", params=params)
            resp.raise_for_status()
            return resp.json()

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        data = self._get(f"profile/{ticker}")
        if not data:
            raise ValueError(f"No FMP profile for {ticker}")
        p = data[0]
        today = date.today()
        return CompanyProfile(
            ticker=ticker,
            market=market,
            name=p.get("companyName", ticker),
            sector=p.get("sector"),
            industry=p.get("industry"),
            market_cap=_f(p.get("mktCap")),
            shares_outstanding=_f(p.get("sharesOutstanding")),
            description=p.get("description"),
            exchange=p.get("exchangeShortName") or "NASDAQ",
            currency=p.get("currency") or "USD",
            provenance=_prov(today),
        )

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        data = self._get(
            f"historical-price-full/{ticker}",
            from_=start_date.isoformat(),
            to=end_date.isoformat(),
        )
        results: list[StockPrice] = []
        for item in data.get("historical", []):
            d = date.fromisoformat(item["date"])
            results.append(
                StockPrice(
                    ticker=ticker,
                    market=market,
                    date=d,
                    open=_f(item.get("open")) or 0.0,
                    high=_f(item.get("high")) or 0.0,
                    low=_f(item.get("low")) or 0.0,
                    close=_f(item.get("close")) or 0.0,
                    adjusted_close=_f(item.get("adjClose")),
                    volume=int(item.get("volume") or 0),
                    provenance=_prov(d),
                )
            )
        return sorted(results, key=lambda x: x.date)

    def get_income_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[IncomeStatement]:
        period = "annual" if period_type == "annual" else "quarter"
        data = self._get(f"income-statement/{ticker}", period=period, limit=limit)
        results: list[IncomeStatement] = []
        for item in data:
            d = date.fromisoformat(item["date"])
            rev = _f(item.get("revenue"))
            if rev is None:
                continue
            cogs = _f(item.get("costOfRevenue")) or 0.0
            results.append(
                IncomeStatement(
                    ticker=ticker,
                    fiscal_year=d.year,
                    fiscal_quarter=item.get("period", "FY").replace("Q", "") if "Q" in str(item.get("period", "")) else None,
                    period_type=period_type,
                    period_end_date=d,
                    revenue=rev,
                    cost_of_revenue=cogs,
                    gross_profit=_f(item.get("grossProfit")) or (rev - cogs),
                    operating_income=_f(item.get("operatingIncome")) or 0.0,
                    ebitda=_f(item.get("ebitda")),
                    interest_expense=_f(item.get("interestExpense")),
                    pretax_income=_f(item.get("incomeBeforeTax")) or 0.0,
                    income_tax=_f(item.get("incomeTaxExpense")),
                    net_income=_f(item.get("netIncome")) or 0.0,
                    eps_basic=_f(item.get("eps")),
                    eps_diluted=_f(item.get("epsdiluted")),
                    shares_basic=_f(item.get("weightedAverageShsOut")) or 1.0,
                    shares_diluted=_f(item.get("weightedAverageShsOutDil")),
                    provenance=_prov(d),
                )
            )
        return sorted(results, key=lambda x: x.period_end_date)

    def get_balance_sheets(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[BalanceSheet]:
        period = "annual" if period_type == "annual" else "quarter"
        data = self._get(f"balance-sheet-statement/{ticker}", period=period, limit=limit)
        results: list[BalanceSheet] = []
        for item in data:
            d = date.fromisoformat(item["date"])
            total_assets = _f(item.get("totalAssets"))
            if total_assets is None:
                continue
            results.append(
                BalanceSheet(
                    ticker=ticker,
                    period_end_date=d,
                    period_type=period_type,
                    total_assets=total_assets,
                    current_assets=_f(item.get("totalCurrentAssets")) or 0.0,
                    cash_and_equivalents=_f(item.get("cashAndCashEquivalents")) or 0.0,
                    accounts_receivable=_f(item.get("netReceivables")),
                    inventory=_f(item.get("inventory")),
                    non_current_assets=_f(item.get("totalNonCurrentAssets")),
                    total_liabilities=_f(item.get("totalLiabilities")) or 0.0,
                    current_liabilities=_f(item.get("totalCurrentLiabilities")) or 0.0,
                    short_term_debt=_f(item.get("shortTermDebt")),
                    accounts_payable=_f(item.get("accountPayables")),
                    long_term_debt=_f(item.get("longTermDebt")),
                    total_equity=_f(item.get("totalStockholdersEquity")) or 0.0,
                    retained_earnings=_f(item.get("retainedEarnings")),
                    provenance=_prov(d),
                )
            )
        return sorted(results, key=lambda x: x.period_end_date)

    def get_cash_flow_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[CashFlowStatement]:
        period = "annual" if period_type == "annual" else "quarter"
        data = self._get(f"cash-flow-statement/{ticker}", period=period, limit=limit)
        results: list[CashFlowStatement] = []
        for item in data:
            d = date.fromisoformat(item["date"])
            ocf = _f(item.get("operatingCashFlow"))
            if ocf is None:
                continue
            capex = _f(item.get("capitalExpenditure")) or 0.0
            results.append(
                CashFlowStatement(
                    ticker=ticker,
                    fiscal_year=d.year,
                    period_type=period_type,
                    period_end_date=d,
                    operating_cash_flow=ocf,
                    capex=capex,
                    investing_cash_flow=_f(item.get("investingActivitiesCashFlow")) or 0.0,
                    financing_cash_flow=_f(item.get("financingActivitiesCashFlow")) or 0.0,
                    dividends_paid=_f(item.get("dividendsPaid")),
                    stock_repurchases=_f(item.get("commonStockRepurchased")),
                    provenance=_prov(d),
                )
            )
        return sorted(results, key=lambda x: x.period_end_date)
