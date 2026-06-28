"""Shared pytest fixtures for all test layers."""
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from unittest.mock import MagicMock

import pytest

from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DataProvenance,
    IncomeStatement,
    StockPrice,
)

_FIXTURES = Path(__file__).parent / "fixtures"


def _prov(source: str, yr: int) -> DataProvenance:
    return DataProvenance(
        source=source,
        as_of_date=date(yr, 12, 31),
        fetched_at=datetime(yr, 12, 31, tzinfo=timezone.utc),
    )


# --- Fixture data builders ---

def _make_income(ticker: str, yr: int) -> IncomeStatement:
    rev = 1_000_000 * (1.1 ** (yr - 2019))
    return IncomeStatement(
        ticker=ticker, fiscal_year=yr, period_type="annual",
        period_end_date=date(yr, 12, 31),
        revenue=rev, cost_of_revenue=rev * 0.55, gross_profit=rev * 0.45,
        operating_income=rev * 0.15, ebitda=rev * 0.20,
        interest_expense=rev * 0.01, pretax_income=rev * 0.14,
        income_tax=rev * 0.03, net_income=rev * 0.11,
        eps_basic=rev * 0.11 / 1_000_000, eps_diluted=rev * 0.11 / 1_050_000,
        shares_basic=1_000_000, shares_diluted=1_050_000,
        provenance=_prov("yfinance", yr),
    )


def _make_balance(ticker: str, yr: int) -> BalanceSheet:
    assets = 5_000_000 * (1.05 ** (yr - 2019))
    return BalanceSheet(
        ticker=ticker, period_end_date=date(yr, 12, 31), period_type="annual",
        total_assets=assets, current_assets=assets * 0.35,
        cash_and_equivalents=assets * 0.10, accounts_receivable=assets * 0.12,
        inventory=assets * 0.08, non_current_assets=assets * 0.65,
        total_liabilities=assets * 0.45, current_liabilities=assets * 0.15,
        short_term_debt=assets * 0.05, accounts_payable=assets * 0.06,
        long_term_debt=assets * 0.20, total_equity=assets * 0.55,
        retained_earnings=assets * 0.30,
        provenance=_prov("yfinance", yr),
    )


def _make_cashflow(ticker: str, yr: int) -> CashFlowStatement:
    ocf = 200_000 * (1.08 ** (yr - 2019))
    return CashFlowStatement(
        ticker=ticker, fiscal_year=yr, period_type="annual",
        period_end_date=date(yr, 12, 31),
        operating_cash_flow=ocf, capex=-ocf * 0.30,
        investing_cash_flow=-ocf * 0.35, financing_cash_flow=-ocf * 0.20,
        dividends_paid=-ocf * 0.15,
        provenance=_prov("yfinance", yr),
    )


def _make_prices(ticker: str, market: Literal["KR", "US"]) -> list[StockPrice]:
    base = 150.0 if market == "US" else 70_000.0
    prices = []
    for i in range(252):
        d = date(2025, 1, 1)
        from datetime import timedelta
        d = date(2025, 1, 1) + timedelta(days=i)
        prices.append(StockPrice(
            ticker=ticker, market=market, date=d,
            open=base + i * 0.1, high=base + i * 0.1 + 2,
            low=base + i * 0.1 - 2, close=base + i * 0.1,
            volume=10_000_000,
            provenance=_prov("yfinance", 2025),
        ))
    return prices


# --- Fixtures ---

@pytest.fixture()
def aapl_income():
    return [_make_income("AAPL", yr) for yr in range(2020, 2025)]


@pytest.fixture()
def aapl_balance():
    return [_make_balance("AAPL", yr) for yr in range(2020, 2025)]


@pytest.fixture()
def aapl_cashflow():
    return [_make_cashflow("AAPL", yr) for yr in range(2020, 2025)]


@pytest.fixture()
def aapl_prices():
    return _make_prices("AAPL", "US")


@pytest.fixture()
def aapl_profile():
    return CompanyProfile(
        ticker="AAPL", market="US", name="Apple Inc.",
        sector="Technology", industry="Consumer Electronics",
        market_cap=3_000_000_000_000.0, shares_outstanding=15_500_000_000.0,
        exchange="NASDAQ", currency="USD",
        provenance=_prov("yfinance", 2025),
    )


@pytest.fixture()
def samsung_profile():
    return CompanyProfile(
        ticker="005930", market="KR", name="삼성전자",
        name_en="Samsung Electronics",
        sector="Technology", industry="Semiconductors",
        market_cap=400_000_000_000_000.0, shares_outstanding=5_969_782_550.0,
        exchange="KRX", currency="KRW",
        dart_corp_code="00126380",
        provenance=_prov("dart", 2025),
    )


@pytest.fixture()
def mock_data_gateway(aapl_income, aapl_balance, aapl_cashflow, aapl_prices, aapl_profile):
    gw = MagicMock()
    gw.get_company_profile.return_value = aapl_profile
    gw.get_income_statements.return_value = aapl_income
    gw.get_balance_sheets.return_value = aapl_balance
    gw.get_cash_flow_statements.return_value = aapl_cashflow
    gw.get_price_history.return_value = aapl_prices
    return gw
