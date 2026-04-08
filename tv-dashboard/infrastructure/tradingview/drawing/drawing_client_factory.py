from config import trading_view_username, trading_view_password, trading_view_layout_id, owner_source
from infrastructure.tradingview.authentication.trading_view_authentifier import TradingViewAuthentifier
from infrastructure.tradingview.data.trading_view_data_client import TradingViewDataClient
from infrastructure.tradingview.drawing.trading_view_drawing_api_client import TradingViewDrawingApiClient
from infrastructure.tradingview.drawing.trading_view_id_generator import TradingViewIdGenerator
from infrastructure.tradingview.drawing.trading_view_jwt_client import TradingViewJwtClient
from infrastructure.tradingview.drawing.trading_view_request_parameters import TradingViewRequestParameters
from infrastructure.tradingview.time_frames.time_frame_converter import TradingViewTimeFrameConverter
from infrastructure.tradingview.trends.trend_converter import TradingViewTrendConverter


def create_drawing_client(trading_view_symbol: str):
    trading_view_authentifier = TradingViewAuthentifier()
    trading_view_session = trading_view_authentifier.login(
        username=trading_view_username,
        password=trading_view_password
    )
    trading_view_id_generator = TradingViewIdGenerator()
    jwt_client = TradingViewJwtClient()
    client_id = trading_view_id_generator.create_client_id()
    jwt = jwt_client.get_chart_token(
        user_id=trading_view_session.user_id,
        session_id=trading_view_session.session_id,
        layout_id=trading_view_layout_id,
        symbol=trading_view_symbol
    )
    request_parameters = TradingViewRequestParameters(
        client_id=client_id,
        layout_id=trading_view_layout_id,
        owner_source=owner_source,
        session=trading_view_session,
        jwt=jwt
    )
    drawing_client = TradingViewDrawingApiClient(
        parameters=request_parameters,
        trading_view_id_generator=trading_view_id_generator,
        trading_view_trend_converter=TradingViewTrendConverter()
    )

    return drawing_client


def create_drawing_client_and_data_client(trading_view_symbol: str):
    trading_view_authentifier = TradingViewAuthentifier()
    trading_view_session = trading_view_authentifier.login(
        username=trading_view_username,
        password=trading_view_password
    )
    trading_view_data_client = TradingViewDataClient(
        trading_view_time_frame_converter=TradingViewTimeFrameConverter()
    )
    trading_view_id_generator = TradingViewIdGenerator()
    jwt_client = TradingViewJwtClient()
    client_id = trading_view_id_generator.create_client_id()
    jwt = jwt_client.get_chart_token(
        user_id=trading_view_session.user_id,
        session_id=trading_view_session.session_id,
        layout_id=trading_view_layout_id,
        symbol=trading_view_symbol
    )
    request_parameters = TradingViewRequestParameters(
        client_id=client_id,
        layout_id=trading_view_layout_id,
        owner_source=owner_source,
        session=trading_view_session,
        jwt=jwt
    )
    drawing_client = TradingViewDrawingApiClient(
        parameters=request_parameters,
        trading_view_id_generator=trading_view_id_generator,
        trading_view_trend_converter=TradingViewTrendConverter()
    )

    return drawing_client, trading_view_data_client
