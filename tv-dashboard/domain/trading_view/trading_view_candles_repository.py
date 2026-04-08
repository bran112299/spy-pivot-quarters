import abc
from typing import List

from domain.candles.candle import Candle


class TradingViewCandlesRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, ticker: str, interval: str, candles: List[Candle]):
        pass
