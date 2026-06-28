"""Integration tests for the Jinja2 report renderer."""
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.report_service.models import AnalysisReport, ReportSection
from services.report_service.renderer import render, save
from services.data_gateway.models import DataProvenance
from datetime import date


@pytest.fixture()
def sample_report():
    prov = DataProvenance(
        source="yfinance",
        as_of_date=date(2025, 6, 25),
        fetched_at=datetime(2025, 6, 25, 10, 0, tzinfo=timezone.utc),
    )
    sections = [
        ReportSection(
            section_id="executive_summary",
            title="Executive Summary",
            content="Apple demonstrates strong revenue growth of 10% YoY.",
        ),
        ReportSection(
            section_id="company_overview",
            title="Company Overview",
            content="Apple Inc. is a technology company.",
        ),
    ]
    return AnalysisReport(
        report_id="test-report-001",
        ticker="AAPL",
        market="US",
        company_name="Apple Inc.",
        generated_at=datetime(2025, 6, 25, 10, 0, tzinfo=timezone.utc),
        sections=sections,
        data_provenance_summary=[prov],
        model_id="claude-sonnet-4-6",
        warnings=[],
    )


class TestMarkdownRenderer:
    def test_render_produces_string(self, sample_report):
        output = render(sample_report, "markdown")
        assert isinstance(output, str)
        assert len(output) > 0

    def test_render_includes_ticker(self, sample_report):
        output = render(sample_report, "markdown")
        assert "AAPL" in output

    def test_render_includes_company_name(self, sample_report):
        output = render(sample_report, "markdown")
        assert "Apple Inc." in output

    def test_render_includes_section_headings(self, sample_report):
        output = render(sample_report, "markdown")
        assert "## Executive Summary" in output
        assert "## Company Overview" in output

    def test_render_includes_section_content(self, sample_report):
        output = render(sample_report, "markdown")
        assert "10% YoY" in output

    def test_render_includes_provenance_table(self, sample_report):
        output = render(sample_report, "markdown")
        assert "yfinance" in output
        assert "2025-06-25" in output

    def test_render_includes_model_id(self, sample_report):
        output = render(sample_report, "markdown")
        assert "claude-sonnet-4-6" in output


class TestHTMLRenderer:
    def test_render_html_produces_valid_html(self, sample_report):
        output = render(sample_report, "html")
        assert "<!DOCTYPE html>" in output
        assert "<html" in output
        assert "</html>" in output

    def test_render_html_includes_ticker(self, sample_report):
        output = render(sample_report, "html")
        assert "AAPL" in output

    def test_render_html_includes_sections(self, sample_report):
        output = render(sample_report, "html")
        assert "Executive Summary" in output

    def test_render_html_includes_provenance_table(self, sample_report):
        output = render(sample_report, "html")
        assert "yfinance" in output
        assert "<table" in output


class TestSaveRenderer:
    def test_save_creates_markdown_file(self, sample_report, tmp_path):
        path = save(sample_report, tmp_path, "markdown")
        assert path.exists()
        assert path.suffix == ".md"
        assert "AAPL" in path.name

    def test_save_creates_html_file(self, sample_report, tmp_path):
        path = save(sample_report, tmp_path, "html")
        assert path.exists()
        assert path.suffix == ".html"

    def test_save_file_has_content(self, sample_report, tmp_path):
        path = save(sample_report, tmp_path, "markdown")
        content = path.read_text(encoding="utf-8")
        assert "Apple Inc." in content

    def test_save_creates_output_dir_if_missing(self, sample_report, tmp_path):
        new_dir = tmp_path / "nested" / "reports"
        path = save(sample_report, new_dir, "markdown")
        assert new_dir.exists()
        assert path.exists()

    def test_report_with_warnings_includes_them(self, sample_report, tmp_path):
        sample_report.warnings = ["DART API unavailable"]
        output = render(sample_report, "markdown")
        assert "DART API unavailable" in output
