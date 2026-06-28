"""StockAnalysisAgent — manages the Anthropic tool_use loop."""
import uuid
from datetime import datetime, timezone
from typing import Literal

import anthropic

from config.settings import Settings
from services.calculation_engine.engine import CalculationEngine
from services.data_gateway.models import DataProvenance
from services.data_gateway.registry import DataGateway
from services.report_service.models import AnalysisReport, ReportSection
from services.report_service.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from services.report_service.tools import TOOL_DEFINITIONS, ToolExecutor


class StockAnalysisAgent:
    def __init__(
        self,
        settings: Settings,
        gateway: DataGateway,
        engine: CalculationEngine,
        anthropic_client: anthropic.Anthropic | None = None,
    ) -> None:
        self._client = anthropic_client or anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._settings = settings
        self._executor = ToolExecutor(gateway, engine)

    def analyze(self, ticker: str, market: Literal["KR", "US"]) -> AnalysisReport:
        extra_section = "Corporate Disclosures" if market == "KR" else "Industry Context"
        user_message = USER_PROMPT_TEMPLATE.format(ticker=ticker, market=market, extra_section=extra_section)

        messages: list[dict] = [{"role": "user", "content": user_message}]
        all_provenance: list[DataProvenance] = []
        warnings: list[str] = []
        company_name = ticker
        model_id = self._settings.claude_model

        while True:
            response = self._client.messages.create(
                model=self._settings.claude_model,
                max_tokens=self._settings.max_tokens_per_response,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
            model_id = response.model

            if response.stop_reason == "end_turn":
                narrative = _extract_text(response.content)
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        try:
                            result_data, provenance = self._executor.execute(block.name, block.input)
                            all_provenance.extend(provenance)
                            # Capture company name from profile call
                            if block.name == "get_company_profile":
                                company_name = result_data.get("name", ticker)
                        except Exception as exc:
                            result_data = {"error": str(exc)}
                            warnings.append(f"Tool {block.name} failed: {exc}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": _to_json_str(result_data),
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason
                narrative = _extract_text(response.content) or ""
                warnings.append(f"Unexpected stop_reason: {response.stop_reason}")
                break

        sections = _parse_sections(narrative)
        unique_provenance = _deduplicate_provenance(all_provenance)

        return AnalysisReport(
            report_id=str(uuid.uuid4()),
            ticker=ticker,
            market=market,
            company_name=company_name,
            generated_at=datetime.now(tz=timezone.utc),
            sections=sections,
            data_provenance_summary=unique_provenance,
            model_id=model_id,
            warnings=warnings,
        )


def _extract_text(content: list) -> str:
    parts = []
    for block in content:
        if hasattr(block, "type") and block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)


def _to_json_str(obj: dict) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)


def _parse_sections(narrative: str) -> list[ReportSection]:
    """Split the LLM narrative into sections by ## headings."""
    import re
    sections: list[ReportSection] = []
    parts = re.split(r"(?m)^## (.+)$", narrative)
    # parts[0] is pre-heading text (preamble), then pairs of (heading, content)
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        section_id = re.sub(r"\W+", "_", title.lower()).strip("_")
        sections.append(ReportSection(section_id=section_id, title=title, content=content))
    return sections


def _deduplicate_provenance(items: list[DataProvenance]) -> list[DataProvenance]:
    seen: set[tuple] = set()
    result: list[DataProvenance] = []
    for p in items:
        key = (p.source, str(p.as_of_date))
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result
