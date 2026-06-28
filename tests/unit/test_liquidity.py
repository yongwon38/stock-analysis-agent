import pytest

from services.calculation_engine.liquidity import cash_ratio, current_ratio, quick_ratio


def test_current_ratio():
    assert current_ratio(200, 100) == pytest.approx(2.0)


def test_current_ratio_zero_liabilities():
    assert current_ratio(200, 0) is None


def test_quick_ratio_with_inventory():
    # (200 - 50) / 100 = 1.5
    assert quick_ratio(200, 50, 100) == pytest.approx(1.5)


def test_quick_ratio_none_inventory_treats_as_zero():
    assert quick_ratio(200, None, 100) == pytest.approx(2.0)


def test_cash_ratio():
    assert cash_ratio(50, 100) == pytest.approx(0.5)


def test_cash_ratio_zero_liabilities():
    assert cash_ratio(50, 0) is None
