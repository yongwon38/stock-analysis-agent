from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from services.calculation_engine.models import TechnicalIndicators
from services.data_gateway.models import DataProvenance, StockPrice


def compute_technical_indicators(
    prices: list[StockPrice],
    source: str = "calculated",
) -> Optional[TechnicalIndicators]:
    if len(prices) < 20:
        return None

    df = pd.DataFrame(
        [
            {
                "date": p.date,
                "close": p.close,
                "high": p.high,
                "low": p.low,
                "volume": p.volume,
            }
            for p in sorted(prices, key=lambda x: x.date)
        ]
    ).set_index("date")

    close = df["close"]
    volume = df["volume"]

    def _sma(n: int) -> Optional[float]:
        if len(close) < n:
            return None
        return float(close.rolling(n).mean().iloc[-1])

    def _ema(span: int) -> Optional[float]:
        if len(close) < span:
            return None
        return float(close.ewm(span=span, adjust=False).mean().iloc[-1])

    def _rsi(n: int = 14) -> Optional[float]:
        if len(close) < n + 1:
            return None
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(n).mean()
        loss = (-delta.clip(upper=0)).rolling(n).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi_series = 100 - (100 / (1 + rs))
        val = rsi_series.iloc[-1]
        return float(val) if pd.notna(val) else None

    def _macd() -> tuple[Optional[float], Optional[float], Optional[float]]:
        if len(close) < 26:
            return None, None, None
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return (
            float(macd_line.iloc[-1]),
            float(signal_line.iloc[-1]),
            float(histogram.iloc[-1]),
        )

    def _bollinger(n: int = 20, k: float = 2.0) -> tuple[Optional[float], Optional[float], Optional[float]]:
        if len(close) < n:
            return None, None, None
        mid = close.rolling(n).mean()
        std = close.rolling(n).std()
        upper = mid + k * std
        lower = mid - k * std
        return float(upper.iloc[-1]), float(mid.iloc[-1]), float(lower.iloc[-1])

    def _volume_ratio(n: int = 20) -> Optional[float]:
        if len(volume) < n:
            return None
        avg_vol = float(volume.rolling(n).mean().iloc[-1])
        return float(volume.iloc[-1]) / avg_vol if avg_vol else None

    def _52w_stats() -> tuple[Optional[float], Optional[float]]:
        window = close.tail(252)
        if len(window) < 2:
            return None, None
        hi = float(window.max())
        lo = float(window.min())
        last = float(close.iloc[-1])
        vs_high = (last - hi) / hi if hi else None
        vs_low = (last - lo) / lo if lo else None
        return vs_high, vs_low

    ema12 = _ema(12)
    ema26 = _ema(26)
    macd_val, macd_sig, macd_hist = _macd()
    bb_upper, bb_mid, bb_lower = _bollinger()
    vs_high, vs_low = _52w_stats()
    last_price = prices[-1]

    return TechnicalIndicators(
        ticker=prices[0].ticker,
        as_of_date=sorted(prices, key=lambda x: x.date)[-1].date,
        close=float(close.iloc[-1]),
        sma_20=_sma(20),
        sma_50=_sma(50),
        sma_200=_sma(200),
        ema_12=ema12,
        ema_26=ema26,
        rsi_14=_rsi(14),
        macd=macd_val,
        macd_signal=macd_sig,
        macd_histogram=macd_hist,
        bb_upper=bb_upper,
        bb_middle=bb_mid,
        bb_lower=bb_lower,
        volume_ratio_20d=_volume_ratio(20),
        price_vs_52w_high=vs_high,
        price_vs_52w_low=vs_low,
        provenance=DataProvenance(
            source=source,
            as_of_date=sorted(prices, key=lambda x: x.date)[-1].date,
            fetched_at=datetime.now(tz=timezone.utc),
        ),
    )
