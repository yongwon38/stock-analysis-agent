from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from services.report_service.models import AnalysisReport


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL, 005930)")
    market: Literal["KR", "US"] = Field(..., description="Market: KR or US")


class AnalyzeResponse(BaseModel):
    report_id: str
    ticker: str
    market: Literal["KR", "US"]
    company_name: str
    generated_at: datetime
    status: Literal["success", "partial"] = "success"
    warnings: list[str] = []
    report: AnalysisReport


class ErrorResponse(BaseModel):
    detail: str
    ticker: Optional[str] = None
    market: Optional[str] = None
