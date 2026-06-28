from services.model_service.base import BaseModelService, ModelInfo, PricePrediction


class StubModelService(BaseModelService):
    def is_available(self) -> bool:
        return False

    def get_model_info(self) -> ModelInfo:
        raise NotImplementedError("No model loaded")

    def predict_price(self, ticker: str, market: str, horizon_days: int) -> PricePrediction:
        raise NotImplementedError("No model loaded")
