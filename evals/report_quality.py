"""Post-generation quality checks for AnalysisReport.

run_quality_checks(report) → list[str]  (empty = no issues)
"""
import re
from typing import Literal

from services.report_service.models import AnalysisReport

_REQUIRED_SECTION_IDS = {
    "executive_summary",
    "company_overview",
    "financial_performance",
    "valuation_analysis",
    "profitability_and_returns",
    "risk_assessment",
    "technical_snapshot",
    "growth_outlook",
}

# Minimum character count per section to catch empty/stub sections
_MIN_SECTION_CHARS = 100

# Regex for numbers that look like ratios or financial figures
_NUMBER_RE = re.compile(r"\b\d+\.?\d*\s*%|\b\d{1,3}(?:,\d{3})+|\b\d+\.\d{2,}\b")


def check_sections(report: AnalysisReport) -> list[str]:
    """Verify that all required section IDs are present and non-trivially short."""
    issues: list[str] = []
    present_ids = {s.section_id for s in report.sections}

    for sid in _REQUIRED_SECTION_IDS:
        if sid not in present_ids:
            issues.append(f"Missing required section: {sid}")

    for section in report.sections:
        if len(section.content.strip()) < _MIN_SECTION_CHARS:
            issues.append(
                f"Section '{section.section_id}' content too short "
                f"({len(section.content.strip())} chars < {_MIN_SECTION_CHARS})"
            )

    return issues


def check_provenance_complete(report: AnalysisReport) -> list[str]:
    """Verify that the provenance table is non-empty."""
    issues: list[str] = []
    if not report.data_provenance_summary:
        issues.append("data_provenance_summary is empty — no data sources recorded")
    sources = {p.source for p in report.data_provenance_summary}
    if not sources:
        issues.append("No provenance sources recorded")
    return issues


def check_no_hallucinated_numbers(report: AnalysisReport) -> list[str]:
    """Best-effort: flag sections that contain numbers but have no supporting_data.

    This cannot guarantee correctness but catches the most obvious case where
    Claude generates a section with financial figures but the tool was never called.
    """
    issues: list[str] = []
    for section in report.sections:
        numbers = _NUMBER_RE.findall(section.content)
        if numbers and not section.supporting_data:
            issues.append(
                f"Section '{section.section_id}' contains {len(numbers)} numeric value(s) "
                f"but has no supporting_data — possible LLM-estimated figures"
            )
    return issues


def run_quality_checks(report: AnalysisReport) -> list[str]:
    """Run all quality checks and return combined issue list."""
    issues: list[str] = []
    issues.extend(check_sections(report))
    issues.extend(check_provenance_complete(report))
    issues.extend(check_no_hallucinated_numbers(report))
    return issues


def assert_quality(report: AnalysisReport, level: Literal["strict", "lenient"] = "lenient") -> None:
    """Raise AssertionError if quality checks fail.

    strict: any issue fails
    lenient: only section-presence and provenance failures fail (hallucination check is advisory)
    """
    all_issues = run_quality_checks(report)
    if level == "strict":
        failing = all_issues
    else:
        failing = check_sections(report) + check_provenance_complete(report)

    if failing:
        raise AssertionError(
            f"Report quality check failed ({len(failing)} issues):\n"
            + "\n".join(f"  - {i}" for i in failing)
        )
