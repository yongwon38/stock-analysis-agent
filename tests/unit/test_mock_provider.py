"""Unit tests for MockProvider — verifies data structure and provenance."""
from datetime import date

import pytest

from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    IncomeStatement,
    StockPrice,
)
from services.data_gateway.providers.mock_provider import MockProvider


@pytest.fixture()
def provider():
    return MockProvider()


class TestMockProviderSourceName:
    def test_source_name_is_mock(self, provider):
        assert provider.source_name == "mock"


class TestCompanyProfile:
    def test_returns_company_profile_instance(self, provider):
        result = provider.get_company_profile("AAPL", "US")
        assert isinstance(result, CompanyProfile)

    def test_known_us_ticker_has_correct_name(self, provider):
        result = provider.get_company_profile("AAPL", "US")
        assert result.name == "Apple Inc."

    def test_unknown_us_ticker_uses_fallback(self, provider):
        result = provider.get_company_profile("FAKE", "US")
        assert "FAKE" in result.name

    def test_kr_ticker_returns_krw_currency(self, provider):
        result = provider.get_company_profile("005930", "KR")
        assert result.currency == "KRW"

    def test_us_ticker_returns_usd_currency(self, provider):
        result = provider.get_company_profile("AAPL", "US")
        assert result.currency == "USD"

    def test_provenance_source_is_mock(self, provider):
        result = provider.get_company_profile("AAPL", "US")
        assert result.provenance.source == "mock"

    def test_market_field_matches_argument(self, provider):
        result = provider.get_company_profile("005930", "KR")
        assert result.market == "KR"


class TestIncomeStatements:
    def test_returns_5_years_by_default(self, provider):
        result = provider.get_income_statements("AAPL", "US")
        assert len(result) == 5

    def test_returns_requested_limit(self, provider):
        result = provider.get_income_statements("AAPL", "US", limit=3)
        assert len(result) == 3

    def test_all_items_are_income_statement_instances(self, provider):
        result = provider.get_income_statements("AAPL", "US")
        assert all(isinstance(s, IncomeStatement) for s in result)

    def test_revenue_is_positive(self, provider):
        result = provider.get_income_statements("AAPL", "US")
        assert all(s.revenue > 0 for s in result)

    def test_provenance_source_is_mock(self, provider):
        result = provider.get_income_statements("AAPL", "US")
        assert all(s.provenance.source == "mock" for s in result)

    def test_revenue_grows_over_time(self, provider):
        result = provider.get_income_statements("AAPL", "US")
        revenues = [s.revenue for s in result]
        assert revenues == sorted(revenues), "Revenue should grow year over year"

    def test_operating_income_positive(self, provider):
        result = provider.get_income_statements("AAPL", "US")
        assert all(s.operating_income > 0 for s in result)


class TestBalanceSheets:
    def test_returns_5_years_by_default(self, provider):
        result = provider.get_balance_sheets("AAPL", "US")
        assert len(result) == 5

    def test_all_items_are_balance_sheet_instances(self, provider):
        result = provider.get_balance_sheets("AAPL", "US")
        assert all(isinstance(s, BalanceSheet) for s in result)

    def test_provenance_source_is_mock(self, provider):
        result = provider.get_balance_sheets("AAPL", "US")
        assert all(s.provenance.source == "mock" for s in result)

    def test_total_assets_exceeds_total_equity(self, provider):
        result = provider.get_balance_sheets("AAPL", "US")
        assert all(s.total_assets > s.total_equity for s in result)


class TestCashFlowStatements:
    def test_returns_5_years_by_default(self, provider):
        result = provider.get_cash_flow_statements("AAPL", "US")
        assert len(result) == 5

    def test_all_items_are_cashflow_instances(self, provider):
        result = provider.get_cash_flow_statements("AAPL", "US")
        assert all(isinstance(s, CashFlowStatement) for s in result)

    def test_free_cash_flow_equals_ocf_minus_abs_capex(self, provider):
        result = provider.get_cash_flow_statements("AAPL", "US")
        for s in result:
            expected = s.operating_cash_flow - abs(s.capex)
            assert abs(s.free_cash_flow - expected) < 1.0, (
                f"FCF={s.free_cash_flow}, OCF={s.operating_cash_flow}, capex={s.capex}"
            )

    def test_operating_cash_flow_is_positive(self, provider):
        result = provider.get_cash_flow_statements("AAPL", "US")
        assert all(s.operating_cash_flow > 0 for s in result)

    def test_provenance_source_is_mock(self, provider):
        result = provider.get_cash_flow_statements("AAPL", "US")
        assert all(s.provenance.source == "mock" for s in result)


class TestPriceHistory:
    def test_returns_list_of_stock_price(self, provider):
        start = date(2025, 1, 2)
        end = date(2025, 3, 31)
        result = provider.get_price_history("AAPL", "US", start, end)
        assert isinstance(result, list)
        assert all(isinstance(p, StockPrice) for p in result)

    def test_close_price_is_positive(self, provider):
        start = date(2025, 1, 2)
        end = date(2025, 3, 31)
        result = provider.get_price_history("AAPL", "US", start, end)
        assert all(p.close > 0 for p in result)

    def test_no_weekend_dates(self, provider):
        start = date(2025, 1, 2)
        end = date(2025, 1, 31)
        result = provider.get_price_history("AAPL", "US", start, end)
        assert all(p.date.weekday() < 5 for p in result)

    def test_provenance_source_is_mock(self, provider):
        start = date(2025, 1, 2)
        end = date(2025, 1, 31)
        result = provider.get_price_history("AAPL", "US", start, end)
        assert all(p.provenance.source == "mock" for p in result)
