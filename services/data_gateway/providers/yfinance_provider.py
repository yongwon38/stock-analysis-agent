from datetime import date, datetime, timezone
from typing import Literal

import yfinance as yf

from services.data_gateway.base import BaseDataProvider
from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DataProvenance,
    IncomeStatement,
    StockPrice,
)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _prov(as_of: date) -> DataProvenance:
    return DataProvenance(source="yfinance", as_of_date=as_of, fetched_at=_now())


class YFinanceProvider(BaseDataProvider):
    @property
    def source_name(self) -> str:
        return "yfinance"

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        info = yf.Ticker(ticker).info
        today = date.today()
        return CompanyProfile(
            ticker=ticker,
            market=market,
            name=info.get("longName") or info.get("shortName") or ticker,
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("marketCap"),
            shares_outstanding=info.get("sharesOutstanding"),
            description=info.get("longBusinessSummary"),
            exchange=info.get("exchange") or "UNKNOWN",
            currency=info.get("currency") or "USD",
            provenance=_prov(today),
        )

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False, progress=False)
        if df.empty:
            return []
        results: list[StockPrice] = []
        for dt, row in df.iterrows():
            d = dt.date() if hasattr(dt, "date") else dt
            results.append(
                StockPrice(
                    ticker=ticker,
                    market=market,
                    date=d,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    adjusted_close=float(row["Adj Close"]) if "Adj Close" in row else None,
                    volume=int(row["Volume"]),
                    provenance=_prov(d),
                )
            )
        return results

    def get_income_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[IncomeStatement]:
        t = yf.Ticker(ticker)
        df = t.financials if period_type == "annual" else t.quarterly_financials
        if df is None or df.empty:
            return []
        results: list[IncomeStatement] = []
        for col in list(df.columns)[:limit]:
            d = col.date() if hasattr(col, "date") else col
            def _g(key: str) -> float | None:
                val = df[col].get(key)
                return float(val) if val is not None and str(val) != "nan" else None
            rev = _g("Total Revenue")
            if rev is None:
                continue
            cogs = _g("Cost Of Revenue") or 0.0
            gross = rev - cogs
            op_inc = _g("Operating Income") or 0.0
            net_inc = _g("Net Income") or 0.0
            results.append(
                IncomeStatement(
                    ticker=ticker,
                    fiscal_year=d.year,
                    period_type=period_type,
                    period_end_date=d,
                    revenue=rev,
                    cost_of_revenue=cogs,
                    gross_profit=gross,
                    operating_income=op_inc,
                    ebitda=_g("EBITDA"),
                    interest_expense=_g("Interest Expense"),
                    pretax_income=_g("Pretax Income") or net_inc,
                    income_tax=_g("Tax Provision"),
                    net_income=net_inc,
                    eps_basic=_g("Basic EPS"),
                    eps_diluted=_g("Diluted EPS"),
                    shares_basic=_g("Basic Average Shares") or 1.0,
                    shares_diluted=_g("Diluted Average Shares"),
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
        t = yf.Ticker(ticker)
        df = t.balance_sheet if period_type == "annual" else t.quarterly_balance_sheet
        if df is None or df.empty:
            return []
        results: list[BalanceSheet] = []
        for col in list(df.columns)[:limit]:
            d = col.date() if hasattr(col, "date") else col
            def _g(key: str) -> float | None:
                val = df[col].get(key)
                return float(val) if val is not None and str(val) != "nan" else None
            total_assets = _g("Total Assets")
            if total_assets is None:
                continue
            results.append(
                BalanceSheet(
                    ticker=ticker,
                    period_end_date=d,
                    period_type=period_type,
                    total_assets=total_assets,
                    current_assets=_g("Current Assets") or 0.0,
                    cash_and_equivalents=_g("Cash And Cash Equivalents") or _g("Cash") or 0.0,
                    accounts_receivable=_g("Accounts Receivable"),
                    inventory=_g("Inventory"),
                    non_current_assets=_g("Total Non Current Assets"),
                    total_liabilities=_g("Total Liabilities Net Minority Interest") or 0.0,
                    current_liabilities=_g("Current Liabilities") or 0.0,
                    short_term_debt=_g("Current Debt"),
                    accounts_payable=_g("Accounts Payable"),
                    long_term_debt=_g("Long Term Debt"),
                    total_equity=_g("Stockholders Equity") or _g("Total Equity Gross Minority Interest") or 0.0,
                    retained_earnings=_g("Retained Earnings"),
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
        t = yf.Ticker(ticker)
        df = t.cashflow if period_type == "annual" else t.quarterly_cashflow
        if df is None or df.empty:
            return []
        results: list[CashFlowStatement] = []
        for col in list(df.columns)[:limit]:
            d = col.date() if hasattr(col, "date") else col
            def _g(key: str) -> float | None:
                val = df[col].get(key)
                return float(val) if val is not None and str(val) != "nan" else None
            ocf = _g("Operating Cash Flow") or _g("Cash Flow From Continuing Operating Activities") or 0.0
            capex = _g("Capital Expenditure") or 0.0
            results.append(
                CashFlowStatement(
                    ticker=ticker,
                    fiscal_year=d.year,
                    period_type=period_type,
                    period_end_date=d,
                    operating_cash_flow=ocf,
                    capex=capex,
                    investing_cash_flow=_g("Investing Cash Flow") or 0.0,
                    financing_cash_flow=_g("Financing Cash Flow") or 0.0,
                    dividends_paid=_g("Cash Dividends Paid"),
                    stock_repurchases=_g("Repurchase Of Capital Stock"),
                    provenance=_prov(d),
                )
            )
        return sorted(results, key=lambda x: x.period_end_date)
