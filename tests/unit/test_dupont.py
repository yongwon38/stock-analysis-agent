import pytest

from services.calculation_engine.dupont import dupont_3factor, equity_multiplier


def test_dupont_3factor_computes_roe():
    # ROE = net_margin * asset_turnover * equity_multiplier
    # = 0.10 * 1.5 * 2.0 = 0.30
    dp = dupont_3factor(0.10, 1.5, 2.0)
    assert dp.roe_computed == pytest.approx(0.30)


def test_dupont_3factor_none_component_skips_roe():
    dp = dupont_3factor(0.10, None, 2.0)
    assert dp.roe_computed is None


def test_equity_multiplier():
    assert equity_multiplier(1000, 400) == pytest.approx(2.5)


def test_equity_multiplier_zero_equity():
    assert equity_multiplier(1000, 0) is None
