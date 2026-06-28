from abc import ABC, abstractmethod
from datetime import date

from pydantic import BaseModel


class BacktestConfig(BaseModel):
    strategy_name: str
    universe: list[str]
    start_date: date
    end_date: date
    initial_capital: float = 100_000_000.0
    benchmark_ticker: str = "069500"


class BacktestResult(BaseModel):
    config: BacktestConfig
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    calmar_ratio: float
    trade_log: list[dict] = []


class BaseBacktestEngine(ABC):
    @abstractmethod
    def run(self, config: BacktestConfig) -> BacktestResult: ...

    @abstractmethod
    def is_available(self) -> bool: ...
