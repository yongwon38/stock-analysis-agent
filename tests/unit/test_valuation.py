import pytest

from services.calculation_engine.valuation import (
    enterprise_value,
    ev_ebitda,
    ev_revenue,
    pb_ratio,
    pe_ratio,
    peg_ratio,
    ps_ratio,
)


class TestPERatio:
    def test_normal(self):
        assert pe_ratio(50_000, 3_000) == pytest.approx(16.667, rel=1e-3)

    def test_zero_eps_returns_none(self):
        assert pe_ratio(50_000, 0.0) is None

    def test_negative_eps_returns_none(self):
        assert pe_ratio(50_000, -500) is None

    def test_none_eps_returns_none(self):
        assert pe_ratio(50_000, None) is None


class TestPBRatio:
    def test_normal(self):
        assert pb_ratio(100.0, 40.0) == pytest.approx(2.5)

    def test_zero_bvps_returns_none(self):
        assert pb_ratio(100.0, 0.0) is None

    def test_none_returns_none(self):
        assert pb_ratio(100.0, None) is None


class TestPSRatio:
    def test_normal(self):
        assert ps_ratio(100.0, 50.0) == pytest.approx(2.0)

    def test_zero_returns_none(self):
        assert ps_ratio(100.0, 0.0) is None


class TestEnterpriseValue:
    def test_normal(self):
        assert enterprise_value(1_000_000, 200_000, 50_000) == pytest.approx(1_150_000)

    def test_net_cash_position(self):
        # cash > debt → EV < market cap
        assert enterprise_value(1_000_000, 50_000, 200_000) == pytest.approx(850_000)


class TestEVEBITDA:
    def test_normal(self):
        assert ev_ebitda(500_000, 50_000) == pytest.approx(10.0)

    def test_zero_ebitda_returns_none(self):
        assert ev_ebitda(500_000, 0.0) is None

    def test_negative_ebitda_returns_none(self):
        assert ev_ebitda(500_000, -10_000) is None


class TestPEGRatio:
    def test_normal(self):
        # P/E=20, growth=10% → PEG = 20 / (0.10 * 100) = 20/10 = 2.0
        assert peg_ratio(20.0, 0.10) == pytest.approx(2.0)

    def test_zero_growth_returns_none(self):
        assert peg_ratio(20.0, 0.0) is None

    def test_none_pe_returns_none(self):
        assert peg_ratio(None, 0.15) is None
