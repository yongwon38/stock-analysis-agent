"""Integration tests for DataGateway routing with mock providers."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.data_gateway.registry import DataGateway

_FIXTURES_US = Path(__file__).parent.parent / "fixtures" / "us"
_FIXTURES_KR = Path(__file__).parent.parent / "fixtures" / "kr"


@pytest.fixture()
def mock_settings(tmp_path):
    s = MagicMock()
    s.cache_dir = tmp_path / "cache"
    s.cache_ttl_seconds = 3600
    s.fmp_api_key = None
    s.alpha_vantage_api_key = None
    s.dart_api_key = None
    return s


@pytest.fixture()
def gateway(mock_settings):
    import sys

    mock_provider = MagicMock()
    mock_provider.source_name = "yfinance"

    mock_yf_module = MagicMock()
    mock_yf_module.YFinanceProvider.return_value = mock_provider

    # Inject mock module so the lazy import inside _register_providers() succeeds
    # without triggering the real yfinance/pandas import chain.
    _key = "services.data_gateway.providers.yfinance_provider"
    _saved = sys.modules.get(_key)
    sys.modules[_key] = mock_yf_module
    try:
        gw = DataGateway(mock_settings)
    finally:
        if _saved is None:
            sys.modules.pop(_key, None)
        else:
            sys.modules[_key] = _saved

    gw._mock_provider = mock_provider
    return gw


def _load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


class TestDataGatewayFixtureFiles:
    def test_aapl_profile_fixture_loads(self):
        data = json.loads((_FIXTURES_US / "aapl_profile.json").read_text(encoding="utf-8"))
        assert data["ticker"] == "AAPL"
        assert data["market"] == "US"
        assert "provenance" in data

    def test_aapl_income_fixture_has_5_years(self):
        data = _load(_FIXTURES_US / "aapl_income.json")
        assert len(data) == 5
        assert all("revenue" in s for s in data)
        assert all("provenance" in s for s in data)

    def test_aapl_balance_fixture_has_5_years(self):
        data = _load(_FIXTURES_US / "aapl_balance.json")
        assert len(data) == 5
        assert all("total_assets" in s for s in data)

    def test_aapl_cashflow_fixture_has_5_years(self):
        data = _load(_FIXTURES_US / "aapl_cashflow.json")
        assert len(data) == 5
        assert all("free_cash_flow" in s for s in data)

    def test_aapl_prices_fixture_has_252_days(self):
        data = _load(_FIXTURES_US / "aapl_prices.json")
        assert len(data) == 252
        assert all("close" in p for p in data)

    def test_samsung_profile_fixture_loads(self):
        data = json.loads((_FIXTURES_KR / "samsung_profile.json").read_text(encoding="utf-8"))
        assert data["ticker"] == "005930"
        assert data["market"] == "KR"
        assert data["currency"] == "KRW"

    def test_samsung_income_fixture_has_5_years(self):
        data = _load(_FIXTURES_KR / "samsung_income.json")
        assert len(data) == 5
        assert all("revenue" in s for s in data)

    def test_all_fixtures_have_provenance(self):
        for fixture_path in list(_FIXTURES_US.glob("*.json")) + list(_FIXTURES_KR.glob("*.json")):
            raw = fixture_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            items = data if isinstance(data, list) else [data]
            for item in items[:1]:
                assert "provenance" in item, f"{fixture_path.name} missing provenance"


class TestDataGatewayProvidersRegistered:
    def test_yfinance_always_registered(self, gateway):
        assert "yfinance" in gateway._providers

    def test_fmp_not_registered_without_key(self, gateway):
        assert "fmp" not in gateway._providers

    def test_dart_not_registered_without_key(self, gateway):
        assert "dart" not in gateway._providers

    def test_us_price_provider_falls_back_to_yfinance(self, gateway):
        provider = gateway._price_provider("US")
        assert provider.source_name == "yfinance"
