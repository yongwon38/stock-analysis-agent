"""Mock analysis pipeline /runs end-to-end without any API keys.

Flow:
  MockProvider → CalculationEngine → pre-built ReportSections → AnalysisReport → renderer
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from services.calculation_engine.engine import CalculationEngine
from services.calculation_engine.models import FinancialRatios
from services.data_gateway.models import CompanyProfile, IncomeStatement
from services.data_gateway.providers.mock_provider import MockProvider
from services.report_service.models import AnalysisReport, ReportSection


def run_mock_analysis(ticker: str, market: Literal["KR", "US"]) -> AnalysisReport:
    """Return an AnalysisReport built from mock data /no Claude API required."""
    provider = MockProvider()

    # 1. Fetch mock data
    profile = provider.get_company_profile(ticker, market)
    income = provider.get_income_statements(ticker, market, limit=5)
    balance = provider.get_balance_sheets(ticker, market, limit=5)
    cashflow = provider.get_cash_flow_statements(ticker, market, limit=5)

    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    prices = provider.get_price_history(ticker, market, start_date, end_date)
    close_price = prices[-1].close if prices else 0.0

    # 2. Calculate ratios
    engine = CalculationEngine()
    ratios = engine.calculate_all(income, balance, cashflow, profile, close_price)

    # 3. Build sections
    sections = _build_sections(profile, ratios, income)

    provenance = [
        income[0].provenance if income else profile.provenance,
        balance[0].provenance if balance else profile.provenance,
        ratios.provenance,
    ]

    return AnalysisReport(
        report_id=f"mock-{ticker.lower()}-{uuid.uuid4().hex[:8]}",
        ticker=ticker,
        market=market,
        company_name=profile.name,
        generated_at=datetime.now(tz=timezone.utc),
        sections=sections,
        data_provenance_summary=provenance,
        model_id="mock (no LLM)",
        warnings=["[Mock Data] 이 리포트는 테스트용 가상 데이터 기반입니다. 실제 투자 판단에 사용하지 마십시오."],
    )


def _fmt(v: float | None, pct: bool = False, decimals: int = 2) -> str:
    if v is None:
        return "N/A"
    if pct:
        return f"{v * 100:.{decimals}f}%"
    if abs(v) >= 1_000_000_000_000:
        return f"{v / 1_000_000_000_000:.2f}T"
    if abs(v) >= 1_000_000_000:
        return f"{v / 1_000_000_000:.2f}B"
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.2f}M"
    return f"{v:.{decimals}f}"


def _build_sections(
    profile: CompanyProfile,
    ratios: FinancialRatios,
    income: list[IncomeStatement],
) -> list[ReportSection]:
    currency = profile.currency
    today = date.today().isoformat()

    # A. 한 줄 요약
    executive = (
        f"**{profile.name}** ({profile.ticker}, {profile.market}) /"
        f"섹터: {profile.sector or 'N/A'}, "
        f"PER: {_fmt(ratios.pe_ratio)}x, "
        f"영업이익률: {_fmt(ratios.operating_margin, pct=True)}, "
        f"부채비율: {_fmt(ratios.debt_to_equity, decimals=1)}x "
        f"(기준일: {today}, 가상 데이터)"
    )

    # B. 기업 개요
    overview = (
        f"| 항목 | 내용 |\n"
        f"|------|------|\n"
        f"| 기업명 | {profile.name} |\n"
        f"| 티커 | {profile.ticker} |\n"
        f"| 시장 | {profile.exchange} ({profile.market}) |\n"
        f"| 섹터 | {profile.sector or 'N/A'} |\n"
        f"| 산업 | {profile.industry or 'N/A'} |\n"
        f"| 시가총액 | {_fmt(profile.market_cap)} {currency} |\n"
        f"| 발행주식수 | {_fmt(profile.shares_outstanding)} 주 |\n"
        f"| 통화 | {currency} |\n"
    )

    # D. 실적 흐름 /5년 매출 표
    rev_rows = "\n".join(
        f"| {s.fiscal_year} | {_fmt(s.revenue)} | {_fmt(s.operating_income)} | "
        f"{_fmt(s.operating_income / s.revenue if s.revenue else None, pct=True)} | "
        f"{_fmt(s.net_income)} | {_fmt(s.net_income / s.revenue if s.revenue else None, pct=True)} |"
        for s in income
    )
    financial_perf = (
        f"| 회계연도 | 매출 ({currency}) | 영업이익 | 영업이익률 | 순이익 | 순이익률 |\n"
        f"|---------|----------------|---------|-----------|-------|--------|\n"
        f"{rev_rows}\n\n"
        f"- 매출 YoY 성장률: {_fmt(ratios.revenue_growth_yoy, pct=True)}\n"
        f"- 매출 3년 CAGR: {_fmt(ratios.revenue_cagr_3y, pct=True)}\n"
    )

    # F. 밸류에이션
    valuation_text = (
        f"| 지표 | 값 |\n"
        f"|------|----|\n"
        f"| PER (주가수익비율) | {_fmt(ratios.pe_ratio)}x |\n"
        f"| PBR (주가순자산비율) | {_fmt(ratios.pb_ratio)}x |\n"
        f"| PSR (주가매출비율) | {_fmt(ratios.ps_ratio)}x |\n"
        f"| EV/EBITDA | {_fmt(ratios.ev_ebitda)}x |\n"
        f"| EV/Revenue | {_fmt(ratios.ev_revenue)}x |\n"
        f"| PEG Ratio | {_fmt(ratios.peg_ratio)}x |\n"
        f"\n> 밸류에이션은 가상 데이터 기반입니다. 실제 시장 가격과 다를 수 있습니다."
    )

    # E. 재무 안정성
    stability_text = (
        f"| 지표 | 값 |\n"
        f"|------|----|\n"
        f"| 유동비율 | {_fmt(ratios.current_ratio)}x |\n"
        f"| 당좌비율 | {_fmt(ratios.quick_ratio)}x |\n"
        f"| 현금비율 | {_fmt(ratios.cash_ratio)}x |\n"
        f"| 부채비율 (D/E) | {_fmt(ratios.debt_to_equity)}x |\n"
        f"| 총자산부채비율 (D/A) | {_fmt(ratios.debt_to_assets, pct=True)} |\n"
        f"| 이자보상배율 | {_fmt(ratios.interest_coverage)}x |\n"
        f"| 순부채/EBITDA | {_fmt(ratios.net_debt_to_ebitda)}x |\n"
    )

    # G. 수익성
    profitability_text = (
        f"| 지표 | 값 |\n"
        f"|------|----|\n"
        f"| 매출총이익률 | {_fmt(ratios.gross_margin, pct=True)} |\n"
        f"| 영업이익률 | {_fmt(ratios.operating_margin, pct=True)} |\n"
        f"| 순이익률 | {_fmt(ratios.net_margin, pct=True)} |\n"
        f"| EBITDA 마진 | {_fmt(ratios.ebitda_margin, pct=True)} |\n"
        f"| ROE | {_fmt(ratios.roe, pct=True)} |\n"
        f"| ROA | {_fmt(ratios.roa, pct=True)} |\n"
        f"| ROIC | {_fmt(ratios.roic, pct=True)} |\n"
    )

    # I. 주요 리스크
    risk_text = (
        "**주요 리스크** (가상 데이터 기반 예시)\n\n"
        "- 매크로 리스크: 금리 인상, 환율 변동, 경기 침체 가능성\n"
        "- 산업 리스크: 경쟁 심화, 기술 변화, 규제 리스크\n"
        "- 기업 리스크: 실적 하회, 경영진 리스크, 공급망 이슈\n\n"
        f"> **손실 가능성 고지**: 모든 투자에는 원금 손실 위험이 있습니다. "
        f"이 리포트는 투자 권유가 아닙니다."
    )

    # Data note
    data_note = (
        f"> **[Mock Data]** 이 리포트의 모든 수치는 테스트 목적의 가상 데이터입니다.\n"
        f"> 기준일: {today} | 데이터 출처: mock\n"
        f"> 실제 투자 결정에 사용하지 마십시오."
    )

    return [
        ReportSection(section_id="executive_summary", title="A. 한 줄 요약", content=executive),
        ReportSection(section_id="company_overview", title="B. 기업 개요", content=overview),
        ReportSection(section_id="financial_performance", title="D. 실적 흐름", content=financial_perf),
        ReportSection(section_id="valuation", title="F. 밸류에이션", content=valuation_text),
        ReportSection(section_id="risk_assessment", title="E. 재무 안정성", content=stability_text),
        ReportSection(section_id="profitability", title="G. 수익성", content=profitability_text),
        ReportSection(section_id="risk_factors", title="I. 주요 리스크", content=risk_text),
        ReportSection(section_id="data_note", title="데이터 출처", content=data_note),
    ]
