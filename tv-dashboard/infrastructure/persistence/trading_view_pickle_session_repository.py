import os
import pickle

from domain.trading_view.trading_view_session_repository import TradingViewSessionRepository
from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession


class TradingViewPickleSessionRepository(TradingViewSessionRepository):
    def __init__(self, path=None):
        if path is None:
            self.path = os.path.join('cache', 'cookies.pkl')
        else:
            self.path = path

    def save_auth(self, session: TradingViewSession):
        if not os.path.exists('cache'):
            os.mkdir('cache')
        with open(self.path, 'wb+') as f:
            pickle.dump(session.to_dict(), f)

    def load_auth(self) -> TradingViewSession:
        with open(self.path, 'rb') as f:
            return TradingViewSession.from_dict(pickle.load(f))
