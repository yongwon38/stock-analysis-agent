import pytest

from services.calculation_engine.profitability import (
    avg,
    ebitda_margin,
    gross_margin,
    net_margin,
    operating_margin,
    roa,
    roe,
    roic,
)


def test_gross_margin():
    assert gross_margin(300, 1000) == pytest.approx(0.30)


def test_gross_margin_zero_revenue_returns_none():
    assert gross_margin(300, 0) is None


def test_operating_margin():
    assert operating_margin(150, 1000) == pytest.approx(0.15)


def test_net_margin():
    assert net_margin(100, 1000) == pytest.approx(0.10)


def test_ebitda_margin():
    assert ebitda_margin(200, 1000) == pytest.approx(0.20)


def test_ebitda_margin_none_ebitda():
    assert ebitda_margin(None, 1000) is None


def test_roe():
    assert roe(100, 500) == pytest.approx(0.20)


def test_roe_zero_equity():
    assert roe(100, 0) is None


def test_roa():
    assert roa(100, 2000) == pytest.approx(0.05)


def test_roic():
    # NOPAT = 200 * (1 - 0.21) = 158; invested_capital = 500 + 300 - 100 = 700
    result = roic(ebit=200, tax_rate=0.21, total_debt=300, total_equity=500, cash=100)
    assert result == pytest.approx(158 / 700, rel=1e-3)


def test_roic_zero_invested_capital():
    assert roic(ebit=200, tax_rate=0.21, total_debt=0, total_equity=0, cash=0) is None


def test_avg_normal():
    assert avg(100.0, 200.0) == pytest.approx(150.0)


def test_avg_none_returns_none():
    assert avg(None, 200.0) is None
    assert avg(100.0, None) is None
