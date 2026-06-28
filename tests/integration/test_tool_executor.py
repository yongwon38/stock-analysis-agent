"""Integration tests for ToolExecutor using mock gateway + real CalculationEngine."""
import pytest

from services.calculation_engine.engine import CalculationEngine
from services.calculation_engine.models import FinancialRatios, TechnicalIndicators
from services.report_service.tools import ToolExecutor


@pytest.fixture()
def executor(mock_data_gateway):
    return ToolExecutor(mock_data_gateway, CalculationEngine())


def test_calculate_financial_ratios_returns_financial_ratios(executor):
    result, provenance = executor.execute("calculate_financial_ratios", {"ticker": "AAPL", "market": "US"})
    # Should return a dict (model_dump result); check key presence
    assert "pe_ratio" in result
    assert "roe" in result
    assert "current_ratio" in result
    assert len(provenance) > 0


def test_calculate_technical_indicators_returns_indicators(executor, aapl_prices, mock_data_gateway):
    import sys
    from datetime import date, datetime, timezone
    from unittest.mock import MagicMock
    from services.calculation_engine.models import TechnicalIndicators
    from services.data_gateway.models import DataProvenance

    mock_data_gateway.get_price_history.return_value = aapl_prices

    prov = DataProvenance(
        source="yfinance",
        as_of_date=date.today(),
        fetched_at=datetime.now(timezone.utc),
    )
    mock_indicators = TechnicalIndicators(
        ticker="AAPL",
        as_of_date=date.today(),
        close=152.0,
        sma_20=150.0,
        sma_50=145.0,
        sma_200=140.0,
        ema_12=151.0,
        ema_26=148.0,
        rsi_14=55.0,
        provenance=prov,
    )

    mock_tech_module = MagicMock()
    mock_tech_module.compute_technical_indicators.return_value = mock_indicators

    # Inject mock so the lazy import inside _calculate_technical_indicators succeeds
    # without triggering the real pandas import chain.
    _key = "services.calculation_engine.technical"
    _saved = sys.modules.get(_key)
    sys.modules[_key] = mock_tech_module
    try:
        result, provenance = executor.execute("calculate_technical_indicators", {"ticker": "AAPL", "market": "US"})
    finally:
        if _saved is None:
            sys.modules.pop(_key, None)
        else:
            sys.modules[_key] = _saved

    assert "rsi_14" in result
    assert "sma_20" in result
    assert "close" in result


def test_get_company_profile_returns_profile(executor):
    result, provenance = executor.execute("get_company_profile", {"ticker": "AAPL", "market": "US"})
    assert result["name"] == "Apple Inc."
    assert result["market"] == "US"
    assert len(provenance) == 1


def test_unknown_tool_returns_error(executor):
    result, provenance = executor.execute("nonexistent_tool", {})
    assert "error" in result
    assert provenance == []
