from typing import Literal

from config.settings import Settings
from services.calculation_engine.engine import CalculationEngine
from services.data_gateway.registry import DataGateway
from services.report_service.agent import StockAnalysisAgent
from services.report_service.models import AnalysisReport
from services.report_service.renderer import save


def run_analysis(
    ticker: str,
    market: Literal["KR", "US"],
    settings: Settings,
    save_report: bool = True,
) -> AnalysisReport:
    gateway = DataGateway(settings)
    engine = CalculationEngine()
    agent = StockAnalysisAgent(settings, gateway, engine)

    report = agent.analyze(ticker, market)

    if save_report:
        save(report, settings.report_output_dir, settings.report_format)

    return report
