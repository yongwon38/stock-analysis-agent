"""Tool definitions and executor for the report agent."""
import json
from datetime import date, timedelta
from typing import Any, Literal

from pydantic import BaseModel

from services.calculation_engine.engine import CalculationEngine
from services.data_gateway.models import DataProvenance
from services.data_gateway.registry import DataGateway

TOOL_DEFINITIONS = [
    {
        "name": "get_company_profile",
        "description": "Fetch company name, sector, industry, exchange, market cap, and shares outstanding.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol"},
                "market": {"type": "string", "enum": ["KR", "US"]},
            },
            "required": ["ticker", "market"],
        },
    },
    {
        "name": "get_price_history",
        "description": "Fetch daily OHLCV price history for a given date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["ticker", "market", "start_date", "end_date"],
        },
    },
    {
        "name": "get_income_statements",
        "description": "Fetch annual income statements (up to 5 years): revenue, margins, EPS.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["ticker", "market"],
        },
    },
    {
        "name": "get_balance_sheets",
        "description": "Fetch annual balance sheets: assets, liabilities, equity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["ticker", "market"],
        },
    },
    {
        "name": "get_cash_flow_statements",
        "description": "Fetch annual cash flow statements: OCF, capex, FCF.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["ticker", "market"],
        },
    },
    {
        "name": "calculate_financial_ratios",
        "description": (
            "Compute all financial ratios: valuation (P/E, P/B, EV/EBITDA), "
            "profitability (margins, ROE, ROA, ROIC), liquidity, leverage, growth (YoY + CAGR), "
            "efficiency, and DuPont decomposition."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
            },
            "required": ["ticker", "market"],
        },
    },
    {
        "name": "calculate_technical_indicators",
        "description": "Compute SMA/EMA, RSI, MACD, Bollinger Bands, volume ratio, and 52-week position.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "market": {"type": "string", "enum": ["KR", "US"]},
            },
            "required": ["ticker", "market"],
        },
    },
    {
        "name": "get_peer_comparison",
        "description": "Compute financial ratios for a list of peer tickers for comparative analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "peer_tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of peer ticker symbols",
                },
                "market": {"type": "string", "enum": ["KR", "US"]},
            },
            "required": ["peer_tickers", "market"],
        },
    },
    {
        "name": "search_dart_filings",
        "description": "Search recent DART filings for a Korean stock (annual reports, quarterly reports, material disclosures).",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["ticker"],
        },
    },
]


class ToolExecutor:
    def __init__(self, gateway: DataGateway, engine: CalculationEngine) -> None:
        self._gw = gateway
        self._engine = engine

    def execute(self, tool_name: str, inputs: dict[str, Any]) -> tuple[dict, list[DataProvenance]]:
        dispatch = {
            "get_company_profile": self._get_company_profile,
            "get_price_history": self._get_price_history,
            "get_income_statements": self._get_income_statements,
            "get_balance_sheets": self._get_balance_sheets,
            "get_cash_flow_statements": self._get_cash_flow_statements,
            "calculate_financial_ratios": self._calculate_financial_ratios,
            "calculate_technical_indicators": self._calculate_technical_indicators,
            "get_peer_comparison": self._get_peer_comparison,
            "search_dart_filings": self._search_dart_filings,
        }
        fn = dispatch.get(tool_name)
        if fn is None:
            return {"error": f"Unknown tool: {tool_name}"}, []
        return fn(**inputs)

    def _get_company_profile(self, ticker: str, market: Literal["KR", "US"]):
        result = self._gw.get_company_profile(ticker, market)
        return result.model_dump(mode="json"), [result.provenance]

    def _get_price_history(self, ticker: str, market: Literal["KR", "US"], start_date: str, end_date: str):
        prices = self._gw.get_price_history(ticker, market, date.fromisoformat(start_date), date.fromisoformat(end_date))
        provenance = [p.provenance for p in prices[:1]]
        return {"prices": [p.model_dump(mode="json") for p in prices[-60:]]}, provenance

    def _get_income_statements(self, ticker: str, market: Literal["KR", "US"], limit: int = 5):
        stmts = self._gw.get_income_statements(ticker, market, limit=limit)
        return {"statements": [s.model_dump(mode="json") for s in stmts]}, [s.provenance for s in stmts]

    def _get_balance_sheets(self, ticker: str, market: Literal["KR", "US"], limit: int = 5):
        stmts = self._gw.get_balance_sheets(ticker, market, limit=limit)
        return {"statements": [s.model_dump(mode="json") for s in stmts]}, [s.provenance for s in stmts]

    def _get_cash_flow_statements(self, ticker: str, market: Literal["KR", "US"], limit: int = 5):
        stmts = self._gw.get_cash_flow_statements(ticker, market, limit=limit)
        return {"statements": [s.model_dump(mode="json") for s in stmts]}, [s.provenance for s in stmts]

    def _calculate_financial_ratios(self, ticker: str, market: Literal["KR", "US"]):
        profile = self._gw.get_company_profile(ticker, market)
        income = self._gw.get_income_statements(ticker, market)
        balance = self._gw.get_balance_sheets(ticker, market)
        cashflow = self._gw.get_cash_flow_statements(ticker, market)

        end = date.today()
        start = end - timedelta(days=5)
        prices = self._gw.get_price_history(ticker, market, start, end)
        close_price = prices[-1].close if prices else 0.0

        ratios = self._engine.calculate_all(income, balance, cashflow, profile, close_price)
        provenance = (
            [p.provenance for p in income[:1]]
            + [p.provenance for p in balance[:1]]
            + [p.provenance for p in cashflow[:1]]
        )
        return ratios.model_dump(mode="json"), provenance

    def _calculate_technical_indicators(self, ticker: str, market: Literal["KR", "US"]):
        from services.calculation_engine.technical import compute_technical_indicators

        end = date.today()
        start = end - timedelta(days=400)
        prices = self._gw.get_price_history(ticker, market, start, end)
        indicators = compute_technical_indicators(prices, source=f"{market.lower()}_price")
        if indicators is None:
            return {"error": "Insufficient price data for technical indicators"}, []
        return indicators.model_dump(mode="json"), [indicators.provenance]

    def _get_peer_comparison(self, peer_tickers: list[str], market: Literal["KR", "US"]):
        results = []
        all_provenance = []
        for peer in peer_tickers:
            try:
                data, prov = self._calculate_financial_ratios(peer, market)
                results.append({"ticker": peer, "ratios": data})
                all_provenance.extend(prov)
            except Exception as e:
                results.append({"ticker": peer, "error": str(e)})
        return {"peers": results}, all_provenance

    def _search_dart_filings(self, ticker: str, limit: int = 10):
        filings = self._gw.get_dart_filings(ticker, limit)
        return {"filings": [f.model_dump(mode="json") for f in filings]}, [f.provenance for f in filings[:1]]
