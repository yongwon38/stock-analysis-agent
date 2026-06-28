"""DataGateway — routes data requests to the appropriate provider.

Provider selection:
  - KR price:       pykrx (primary) → fdr (fallback)
  - KR fundamentals: dart
  - US price:        yfinance (primary) → alpha_vantage (fallback)
  - US fundamentals: fmp (primary) → yfinance (fallback)
"""
import json
from datetime import date
from typing import Literal, Optional

from config.settings import Settings
from services.data_gateway.base import BaseDataProvider
from services.data_gateway.cache import FileCache
from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DARTFiling,
    IncomeStatement,
    StockPrice,
)
class DataGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache = FileCache(settings.cache_dir, settings.cache_ttl_seconds)
        self._providers: dict[str, BaseDataProvider] = {}
        self._register_providers()

    def _register_providers(self) -> None:
        try:
            from services.data_gateway.providers.yfinance_provider import YFinanceProvider
            self._providers["yfinance"] = YFinanceProvider()
        except ImportError:
            pass

        if self._settings.fmp_api_key:
            from services.data_gateway.providers.fmp_provider import FMPProvider
            self._providers["fmp"] = FMPProvider(self._settings.fmp_api_key)

        if self._settings.alpha_vantage_api_key:
            from services.data_gateway.providers.alpha_vantage_provider import AlphaVantageProvider
            self._providers["alpha_vantage"] = AlphaVantageProvider(self._settings.alpha_vantage_api_key)

        try:
            from services.data_gateway.providers.fdr_provider import FDRProvider
            self._providers["fdr"] = FDRProvider()
        except ImportError:
            pass

        try:
            from services.data_gateway.providers.pykrx_provider import PyKRXProvider
            self._providers["pykrx"] = PyKRXProvider()
        except ImportError:
            pass

        if self._settings.dart_api_key:
            from services.data_gateway.providers.dart_provider import DARTProvider
            self._providers["dart"] = DARTProvider(self._settings.dart_api_key)

    def _price_provider(self, market: Literal["KR", "US"]) -> BaseDataProvider:
        if market == "KR":
            return self._providers.get("pykrx") or self._providers.get("fdr") or self._providers["yfinance"]
        return self._providers.get("yfinance") or self._providers.get("alpha_vantage", list(self._providers.values())[0])

    def _fundamentals_provider(self, market: Literal["KR", "US"]) -> BaseDataProvider:
        if market == "KR":
            dart = self._providers.get("dart")
            if not dart:
                raise RuntimeError("DART_API_KEY is required for Korean fundamental data")
            return dart
        return self._providers.get("fmp") or self._providers["yfinance"]

    def _cached(self, key: str, fn):
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = fn()
        self._cache.set(key, _serialize(result))
        return _serialize(result)

    # --- Public interface ---

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        provider = self._fundamentals_provider(market) if market == "KR" else self._price_provider(market)
        key = f"profile_{provider.source_name}_{ticker}"
        cached = self._cache.get(key)
        if cached:
            return CompanyProfile.model_validate(cached)
        result = provider.get_company_profile(ticker, market)
        self._cache.set(key, result.model_dump(mode="json"))
        return result

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        provider = self._price_provider(market)
        key = f"price_{provider.source_name}_{ticker}_{start_date}_{end_date}"
        cached = self._cache.get(key)
        if cached:
            return [StockPrice.model_validate(r) for r in cached]
        result = provider.get_price_history(ticker, market, start_date, end_date)
        self._cache.set(key, [r.model_dump(mode="json") for r in result])
        return result

    def get_income_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[IncomeStatement]:
        provider = self._fundamentals_provider(market)
        key = f"income_{provider.source_name}_{ticker}_{period_type}_{limit}"
        cached = self._cache.get(key)
        if cached:
            return [IncomeStatement.model_validate(r) for r in cached]
        result = provider.get_income_statements(ticker, market, period_type, limit)
        self._cache.set(key, [r.model_dump(mode="json") for r in result])
        return result

    def get_balance_sheets(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[BalanceSheet]:
        provider = self._fundamentals_provider(market)
        key = f"balance_{provider.source_name}_{ticker}_{period_type}_{limit}"
        cached = self._cache.get(key)
        if cached:
            return [BalanceSheet.model_validate(r) for r in cached]
        result = provider.get_balance_sheets(ticker, market, period_type, limit)
        self._cache.set(key, [r.model_dump(mode="json") for r in result])
        return result

    def get_cash_flow_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[CashFlowStatement]:
        provider = self._fundamentals_provider(market)
        key = f"cashflow_{provider.source_name}_{ticker}_{period_type}_{limit}"
        cached = self._cache.get(key)
        if cached:
            return [CashFlowStatement.model_validate(r) for r in cached]
        result = provider.get_cash_flow_statements(ticker, market, period_type, limit)
        self._cache.set(key, [r.model_dump(mode="json") for r in result])
        return result

    def get_dart_filings(self, ticker: str, limit: int = 10) -> list[DARTFiling]:
        dart = self._providers.get("dart")
        if not dart:
            raise RuntimeError("DART_API_KEY is required to fetch DART filings")
        key = f"dart_filings_{ticker}_{limit}"
        cached = self._cache.get(key)
        if cached:
            return [DARTFiling.model_validate(r) for r in cached]
        result = dart.get_dart_filings(ticker, limit)
        self._cache.set(key, [r.model_dump(mode="json") for r in result])
        return result


def _serialize(obj):
    return json.loads(json.dumps(obj, default=str))
