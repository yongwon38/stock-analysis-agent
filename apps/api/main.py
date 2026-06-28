from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.routers.analysis import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from config.settings import Settings
    from services.calculation_engine.engine import CalculationEngine
    from services.data_gateway.registry import DataGateway

    settings = Settings()  # type: ignore[call-arg]
    app.state.settings = settings
    app.state.gateway = DataGateway(settings)
    app.state.engine = CalculationEngine()
    yield
    # Cleanup (none required for current implementation)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stock Analysis Agent API",
        description="Structural equity research for KR and US markets.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(analysis_router)
    return app


app = create_app()
