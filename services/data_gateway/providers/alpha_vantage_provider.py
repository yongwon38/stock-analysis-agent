"""Alpha Vantage provider — US price fallback only."""
from datetime import date, datetime, timezone
from typing import Literal

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

_AV_BASE = "https://www.alphavantage.co/query"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _prov(as_of: date) -> DataProvenance:
    return DataProvenance(source="alpha_vantage", as_of_date=as_of, fetched_at=_now())


class AlphaVantageProvider(BaseDataProvider):
    """US daily price history via Alpha Vantage (fallback when yfinance fails)."""

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    @property
    def source_name(self) -> str:
        return "alpha_vantage"

    def _get(self, **params) -> dict:
        params["apikey"] = self._key
        with httpx.Client(timeout=30) as client:
            resp = client.get(_AV_BASE, params=params)
            resp.raise_for_status()
            return resp.json()

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        data = self._get(function="OVERVIEW", symbol=ticker)
        today = date.today()
        return CompanyProfile(
            ticker=ticker,
            market=market,
            name=data.get("Name", ticker),
            sector=data.get("Sector"),
            industry=data.get("Industry"),
            description=data.get("Description"),
            exchange=data.get("Exchange") or "NASDAQ",
            currency=data.get("Currency") or "USD",
            provenance=_prov(today),
        )

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        data = self._get(function="TIME_SERIES_DAILY_ADJUSTED", symbol=ticker, outputsize="full")
        ts = data.get("Time Series (Daily)", {})
        results: list[StockPrice] = []
        for date_str, ohlcv in ts.items():
            d = date.fromisoformat(date_str)
            if not (start_date <= d <= end_date):
                continue
            results.append(
                StockPrice(
                    ticker=ticker,
                    market=market,
                    date=d,
                    open=float(ohlcv["1. open"]),
                    high=float(ohlcv["2. high"]),
                    low=float(ohlcv["3. low"]),
                    close=float(ohlcv["4. close"]),
                    adjusted_close=float(ohlcv["5. adjusted close"]),
                    volume=int(ohlcv["6. volume"]),
                    provenance=_prov(d),
                )
            )
        return sorted(results, key=lambda x: x.date)

    def get_income_statements(self, ticker, market, period_type="annual", limit=5):
        raise NotImplementedError("AlphaVantageProvider does not provide income statements; use FMPProvider")

    def get_balance_sheets(self, ticker, market, period_type="annual", limit=5):
        raise NotImplementedError("AlphaVantageProvider does not provide balance sheets; use FMPProvider")

    def get_cash_flow_statements(self, ticker, market, period_type="annual", limit=5):
        raise NotImplementedError("AlphaVantageProvider does not provide cash flows; use FMPProvider")
