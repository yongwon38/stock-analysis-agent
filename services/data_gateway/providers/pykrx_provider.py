"""pykrx provider — KRX official price and investor-type data."""
from datetime import date, datetime, timezone
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


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _prov(as_of: date) -> DataProvenance:
    return DataProvenance(source="pykrx", as_of_date=as_of, fetched_at=_now())


class PyKRXProvider(BaseDataProvider):
    """KRX official price history via pykrx.

    Does not provide fundamentals — use DARTProvider for those.
    """

    @property
    def source_name(self) -> str:
        return "pykrx"

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        from pykrx import stock as krx

        today = date.today()
        try:
            name = krx.get_market_ticker_name(ticker)
            df = krx.get_market_cap_by_ticker(today.strftime("%Y%m%d"))
            mc = None
            shares = None
            if ticker in df.index:
                mc = float(df.loc[ticker, "시가총액"])
                shares = float(df.loc[ticker, "상장주식수"])
        except Exception:
            name = ticker
            mc = None
            shares = None

        return CompanyProfile(
            ticker=ticker,
            market="KR",
            name=name or ticker,
            exchange="KRX",
            currency="KRW",
            market_cap=mc,
            shares_outstanding=shares,
            provenance=_prov(today),
        )

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        from pykrx import stock as krx

        df = krx.get_market_ohlcv_by_date(
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d"),
            ticker,
        )
        if df is None or df.empty:
            return []
        results: list[StockPrice] = []
        for dt, row in df.iterrows():
            d = dt.date() if hasattr(dt, "date") else dt
            results.append(
                StockPrice(
                    ticker=ticker,
                    market="KR",
                    date=d,
                    open=float(row.get("시가", 0)),
                    high=float(row.get("고가", 0)),
                    low=float(row.get("저가", 0)),
                    close=float(row.get("종가", 0)),
                    volume=int(row.get("거래량", 0)),
                    provenance=_prov(d),
                )
            )
        return results

    def get_income_statements(self, ticker, market, period_type="annual", limit=5):
        raise NotImplementedError("PyKRXProvider does not provide income statements; use DARTProvider")

    def get_balance_sheets(self, ticker, market, period_type="annual", limit=5):
        raise NotImplementedError("PyKRXProvider does not provide balance sheets; use DARTProvider")

    def get_cash_flow_statements(self, ticker, market, period_type="annual", limit=5):
        raise NotImplementedError("PyKRXProvider does not provide cash flows; use DARTProvider")
