from fastapi import APIRouter, HTTPException, Request

from apps.api.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from pipelines.analysis_pipeline import run_analysis

router = APIRouter(prefix="/v1", tags=["analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Generate a stock analysis report",
)
def analyze(body: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    settings = request.app.state.settings
    try:
        report = run_analysis(
            ticker=body.ticker,
            market=body.market,
            settings=settings,
            save_report=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    status = "partial" if report.warnings else "success"
    return AnalyzeResponse(
        report_id=report.report_id,
        ticker=report.ticker,
        market=report.market,
        company_name=report.company_name,
        generated_at=report.generated_at,
        status=status,
        warnings=report.warnings,
        report=report,
    )


@router.get(
    "/health",
    summary="Health check",
)
def health() -> dict:
    return {"status": "ok"}
