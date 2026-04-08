from dataclasses import dataclass

from domain.candles.candle import Candle


@dataclass
class TrendPoint:
    candle_index: int
    candle: Candle
