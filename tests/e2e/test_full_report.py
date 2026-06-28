"""End-to-end test: full agent loop with mocked Anthropic client."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from services.calculation_engine.engine import CalculationEngine
from services.report_service.agent import StockAnalysisAgent
from services.report_service.models import AnalysisReport


def _make_settings():
    s = MagicMock()
    s.anthropic_api_key = "sk-test"
    s.claude_model = "claude-sonnet-4-6"
    s.max_tokens_per_response = 4096
    return s


def _make_tool_use_block(tool_name: str, block_id: str, inputs: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.id = block_id
    block.input = inputs
    return block


def _make_text_block(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_response(stop_reason: str, content: list, model: str = "claude-sonnet-4-6"):
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = content
    resp.model = model
    return resp


MOCK_NARRATIVE = """## Executive Summary

Apple Inc. demonstrates strong financial performance with consistent revenue growth.

## Company Overview

Apple is a technology company focused on consumer electronics and software services.

## Financial Performance

Revenue has grown steadily over the past five years.

## Valuation Analysis

Current P/E ratio suggests the stock is priced at a premium to the market.

## Profitability and Returns

Return on equity remains high, reflecting efficient use of shareholder capital.

## Risk Assessment

Key risks include supply chain concentration and regulatory scrutiny.

## Technical Snapshot

The stock trades above its 200-day moving average.

## Industry Context

Apple operates in the highly competitive consumer electronics sector.

## Growth Outlook

Revenue growth is expected to continue driven by services expansion.
"""


@pytest.fixture()
def mock_client():
    tool_use_response = _make_response(
        "tool_use",
        [_make_tool_use_block("get_company_profile", "tu_001", {"ticker": "AAPL", "market": "US"})],
    )
    final_response = _make_response("end_turn", [_make_text_block(MOCK_NARRATIVE)])
    client = MagicMock()
    client.messages.create.side_effect = [tool_use_response, final_response]
    return client


def test_full_report_produces_analysis_report(mock_data_gateway, mock_client):
    settings = _make_settings()
    engine = CalculationEngine()
    agent = StockAnalysisAgent(settings, mock_data_gateway, engine, anthropic_client=mock_client)
    report = agent.analyze("AAPL", "US")

    assert isinstance(report, AnalysisReport)
    assert report.ticker == "AAPL"
    assert report.market == "US"
    assert len(report.sections) == 9


def test_report_has_all_required_sections(mock_data_gateway, mock_client):
    settings = _make_settings()
    agent = StockAnalysisAgent(settings, mock_data_gateway, CalculationEngine(), anthropic_client=mock_client)
    report = agent.analyze("AAPL", "US")

    section_ids = {s.section_id for s in report.sections}
    assert "executive_summary" in section_ids
    assert "company_overview" in section_ids
    assert "valuation_analysis" in section_ids


def test_report_captures_provenance(mock_data_gateway, mock_client):
    settings = _make_settings()
    agent = StockAnalysisAgent(settings, mock_data_gateway, CalculationEngine(), anthropic_client=mock_client)
    report = agent.analyze("AAPL", "US")

    assert len(report.data_provenance_summary) > 0
    assert all(p.source for p in report.data_provenance_summary)
