from abc import ABC, abstractmethod
from datetime import date

from pydantic import BaseModel


class PricePrediction(BaseModel):
    ticker: str
    market: str
    prediction_date: date
    horizon_days: int
    predicted_price: float
    confidence_interval_low: float
    confidence_interval_high: float
    model_name: str
    model_version: str


class ModelInfo(BaseModel):
    name: str
    version: str
    description: str
    input_features: list[str]
    training_data_end_date: date


class BaseModelService(ABC):
    @abstractmethod
    def predict_price(self, ticker: str, market: str, horizon_days: int) -> PricePrediction: ...

    @abstractmethod
    def get_model_info(self) -> ModelInfo: ...

    @abstractmethod
    def is_available(self) -> bool:
        """Returns False if model weights are not loaded; agent omits the tool."""
        ...
