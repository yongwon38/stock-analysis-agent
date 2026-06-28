import pytest

from services.calculation_engine.leverage import (
    debt_to_assets,
    debt_to_equity,
    interest_coverage,
    net_debt,
    net_debt_to_ebitda,
)


def test_debt_to_equity():
    assert debt_to_equity(300, 700) == pytest.approx(300 / 700)


def test_debt_to_equity_zero_equity():
    assert debt_to_equity(300, 0) is None


def test_debt_to_assets():
    assert debt_to_assets(300, 1000) == pytest.approx(0.30)


def test_interest_coverage():
    assert interest_coverage(500, 100) == pytest.approx(5.0)


def test_interest_coverage_zero_returns_none():
    assert interest_coverage(500, 0) is None


def test_interest_coverage_none_returns_none():
    assert interest_coverage(500, None) is None


def test_net_debt():
    assert net_debt(300, 100) == pytest.approx(200)


def test_net_debt_negative_when_cash_exceeds_debt():
    assert net_debt(100, 300) == pytest.approx(-200)


def test_net_debt_to_ebitda():
    assert net_debt_to_ebitda(300, 100, 100) == pytest.approx(2.0)


def test_net_debt_to_ebitda_zero_ebitda():
    assert net_debt_to_ebitda(300, 100, 0) is None
