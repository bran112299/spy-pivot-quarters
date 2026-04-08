import abc
import datetime

from domain.candles.candles import Candles


class CandlesRepository(abc.ABC):
    @abc.abstractmethod
    def save_candles(self, candles: Candles):
        pass

    @abc.abstractmethod
    def get_candles(self, symbol: str, datetime_end: datetime.datetime):
        pass
