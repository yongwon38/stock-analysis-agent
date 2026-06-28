import pytest

from services.calculation_engine.growth import cagr, compute_cagr, compute_yoy, yoy_growth


def test_yoy_growth_positive():
    assert yoy_growth(110, 100) == pytest.approx(0.10)


def test_yoy_growth_negative():
    assert yoy_growth(90, 100) == pytest.approx(-0.10)


def test_yoy_growth_zero_prior():
    assert yoy_growth(110, 0) is None


def test_cagr():
    # 100 → 161.05 over 5 years ≈ 10% CAGR
    assert cagr(100, 161.051, 5) == pytest.approx(0.10, rel=1e-3)


def test_cagr_zero_years():
    assert cagr(100, 200, 0) is None


def test_cagr_negative_start():
    assert cagr(-100, 200, 5) is None


def test_compute_yoy_two_values():
    assert compute_yoy([100, 115]) == pytest.approx(0.15)


def test_compute_yoy_single_value_returns_none():
    assert compute_yoy([100]) is None


def test_compute_cagr():
    # 3 periods of data → 2-year CAGR by default
    result = compute_cagr([100, 110, 121])
    assert result == pytest.approx(0.10, rel=1e-3)


def test_compute_cagr_explicit_years():
    result = compute_cagr([100, 110, 121, 133], years=3)
    assert result == pytest.approx(0.10, rel=1e-2)
