import abc

from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession


class TradingViewSessionRepository(abc.ABC):
    @abc.abstractmethod
    def save_auth(self, session: TradingViewSession):
        pass

    @abc.abstractmethod
    def load_auth(self) -> TradingViewSession:
        pass
