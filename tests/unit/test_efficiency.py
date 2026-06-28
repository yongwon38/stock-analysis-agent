import pytest

from services.calculation_engine.efficiency import (
    asset_turnover,
    days_inventory_outstanding,
    days_sales_outstanding,
    inventory_turnover,
    receivables_turnover,
)


def test_asset_turnover():
    assert asset_turnover(1000, 500) == pytest.approx(2.0)


def test_asset_turnover_zero_assets():
    assert asset_turnover(1000, 0) is None


def test_inventory_turnover():
    assert inventory_turnover(600, 100) == pytest.approx(6.0)


def test_inventory_turnover_none_inventory():
    assert inventory_turnover(600, None) is None


def test_receivables_turnover():
    assert receivables_turnover(1000, 100) == pytest.approx(10.0)


def test_days_sales_outstanding():
    assert days_sales_outstanding(10.0) == pytest.approx(36.5)


def test_days_sales_outstanding_zero():
    assert days_sales_outstanding(0.0) is None


def test_days_inventory_outstanding():
    assert days_inventory_outstanding(6.0) == pytest.approx(365 / 6)
