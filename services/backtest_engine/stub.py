from services.backtest_engine.base import BaseBacktestEngine, BacktestConfig, BacktestResult


class StubBacktestEngine(BaseBacktestEngine):
    def is_available(self) -> bool:
        return False

    def run(self, config: BacktestConfig) -> BacktestResult:
        raise NotImplementedError("No backtest engine loaded")
