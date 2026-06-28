from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from services.data_gateway.models import DataProvenance


class ReportSection(BaseModel):
    section_id: str
    title: str
    content: str
    supporting_data: dict = {}


class AnalysisReport(BaseModel):
    report_id: str
    ticker: str
    market: Literal["KR", "US"]
    company_name: str
    generated_at: datetime
    sections: list[ReportSection]
    data_provenance_summary: list[DataProvenance]
    model_id: str
    warnings: list[str] = []
