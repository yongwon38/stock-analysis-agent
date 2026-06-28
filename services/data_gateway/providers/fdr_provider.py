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
    return DataProvenance(source="fdr", as_of_date=as_of, fetched_at=_now())


class FDRProvider(BaseDataProvider):
    """FinanceDataReader provider — Korean price history only.

    For KR fundamental data, use DARTProvider alongside this.
    """

    @property
    def source_name(self) -> str:
        return "fdr"

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        import FinanceDataReader as fdr

        today = date.today()
        try:
            listing = fdr.StockListing("KRX")
            row = listing[listing["Code"] == ticker]
            if row.empty:
                name = ticker
                market_cap = None
            else:
                name = str(row.iloc[0].get("Name", ticker))
                market_cap = row.iloc[0].get("Marcap")
                market_cap = float(market_cap) if market_cap else None
        except Exception:
            name = ticker
            market_cap = None

        return CompanyProfile(
            ticker=ticker,
            market="KR",
            name=name,
            exchange="KRX",
            currency="KRW",
            market_cap=market_cap,
            provenance=_prov(today),
        )

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        import FinanceDataReader as fdr

        df = fdr.DataReader(ticker, start=start_date, end=end_date)
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
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    adjusted_close=float(row.get("Adj Close")) if "Adj Close" in row else None,
                    volume=int(row.get("Volume", 0)),
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
        raise NotImplementedError("FDRProvider does not provide income statements; use DARTProvider")

    def get_balance_sheets(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[BalanceSheet]:
        raise NotImplementedError("FDRProvider does not provide balance sheets; use DARTProvider")

    def get_cash_flow_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[CashFlowStatement]:
        raise NotImplementedError("FDRProvider does not provide cash flows; use DARTProvider")
