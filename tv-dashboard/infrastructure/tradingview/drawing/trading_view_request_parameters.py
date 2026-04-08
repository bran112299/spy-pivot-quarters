import dataclasses

from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession


@dataclasses.dataclass
class TradingViewRequestParameters:
    client_id: str
    layout_id: str
    owner_source: str
    jwt: str
    session: TradingViewSession
    chart_id: int = 1
    symbol = 'BINANCE:BTCUSDTPERP'

    def get_session_id(self) -> str:
        return self.session.session_id
