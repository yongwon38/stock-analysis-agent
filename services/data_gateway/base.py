from abc import ABC, abstractmethod
from datetime import date
from typing import Literal

from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DARTFiling,
    IncomeStatement,
    StockPrice,
)


class BaseDataProvider(ABC):
    """All data providers implement this interface."""

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile: ...

    @abstractmethod
    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]: ...

    @abstractmethod
    def get_income_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[IncomeStatement]: ...

    @abstractmethod
    def get_balance_sheets(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[BalanceSheet]: ...

    @abstractmethod
    def get_cash_flow_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[CashFlowStatement]: ...

    def get_dart_filings(self, ticker: str, limit: int = 10) -> list[DARTFiling]:
        """Override in KR-only providers; default raises."""
        raise NotImplementedError(f"{self.source_name} does not support DART filings")
