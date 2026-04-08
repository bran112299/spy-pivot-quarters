import json
import re
from datetime import datetime
from typing import List

from dateutil import relativedelta

from domain.candles.candle import Candle
from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession
from infrastructure.tradingview.time_frames.time_frame_converter import TradingViewTimeFrameConverter
from infrastructure.tradingview.time_frames.trading_view_time_frame import TradingViewTimeFrame


class DataStream:
    def __init__(self, trading_view_time_frame_converter: TradingViewTimeFrameConverter):
        self.trading_view_time_frame_converter: TradingViewTimeFrameConverter = trading_view_time_frame_converter

    def connect(
            self,
            ws,
            trading_view_session: TradingViewSession,
            ticker: str,
            trading_view_time_frame: TradingViewTimeFrame,
            chart_session: str,
            session: str,
            bars_count: int
    ):

        self.send_message(ws, "set_auth_token", [trading_view_session.auth_token])
        self.send_message(ws, "chart_create_session", [chart_session, ""])
        self.send_message(ws, "quote_create_session", [session])
        self.send_message(ws, "quote_set_fields", [
            session, "ch", "chp", "current_session", "description", "local_description", "language",
            "exchange", "fractional", "is_tradable", "lp", "lp_time", "minmov", "minmove2",
            "original_name", "pricescale", "pro_name", "short_name", "type", "update_mode", "volume",
            "currency_code", "rchp", "rtc"
        ])
        self.send_message(ws, "quote_add_symbols", [
            session, ticker, {"flags": ['force_permission']}
        ])
        self.send_message(ws, "quote_fast_symbols", [session, ticker])
        self.send_message(ws, "resolve_symbol", [
            chart_session,
            "symbol_1",
            "={\"symbol\":\"%s\",\"adjustment\":\"splits\",\"session\":\"extended\"}" % ticker
        ])
        self.send_message(ws, "create_series", [
            chart_session, "s1", "s1", "symbol_1", str(trading_view_time_frame.value), bars_count
        ])

    def get_candles(
            self,
            ws,
            ticker: str,
            trading_view_time_frame: TradingViewTimeFrame,
            time_frame_relative_delta: relativedelta
    ) -> List[Candle]:
        websocket_message = self.get_candles_websocket_message(
            ws=ws,
            trading_view_time_frame=trading_view_time_frame
        )

        candles: List[Candle] = self.get_candles_from_websocket_results(
            websocket_result=websocket_message,
            ticker=ticker,
            trading_view_time_frame=trading_view_time_frame,
            time_frame_relative_delta=time_frame_relative_delta
        )

        return candles

    def get_candles_websocket_message(self, trading_view_time_frame: TradingViewTimeFrame, ws):
        ws.recv()
        result = ws.recv()

        next_request_tf = ["720", "240", "60", "15", "5", "3", "1"]
        if trading_view_time_frame.value in next_request_tf:
            result = ws.recv()

        candle_message = None
        while candle_message is None:
            candle_message = re.search(r'"s":\[(.+?)}]', result)
            if candle_message is None:
                print('candle message not received trying again')
                result = ws.recv()

        return result

    def prepend_header(self, st):
        return "~m~" + str(len(st)) + "~m~" + st

    def construct_message(self, func, param_list):
        # json_mylist = json.dumps(mylist, separators=(',', ':'))
        return json.dumps({
            "m": func,
            "p": param_list
        }, separators=(',', ':'))

    def create_message(self, func, param_list: List):
        return self.prepend_header(self.construct_message(func, param_list))

    def send_raw_message(self, ws, message):
        ws.send(self.prepend_header(message))

    def send_message(self, ws, func, args):
        ws.send(self.create_message(func, args))

    def get_candles_from_websocket_results(
            self,
            websocket_result,
            ticker: str,
            trading_view_time_frame: TradingViewTimeFrame,
            time_frame_relative_delta: relativedelta
    ) -> List[Candle]:
        out = re.search(r'"s":\[(.+?)}]', websocket_result)
        raw_candles_from_web_socket = out.group(1).split(',{\"')

        candles: List[Candle] = []
        for raw_candle in raw_candles_from_web_socket:
            raw_candle = re.split(r'[\[:,\]]', raw_candle)
            open_t = datetime.fromtimestamp(abs(float(raw_candle[4])))
            # open_t = datetime.fromtimestamp(float(raw_candle[4]))
            close_t = open_t + time_frame_relative_delta
            open_price = float(raw_candle[5])
            high = float(raw_candle[6])
            low = float(raw_candle[7])
            close = float(raw_candle[8])
            try:
                volume = float(raw_candle[9])
            except:
                volume = 0

            candles.append(Candle(
                symbol=ticker,
                time_frame=self.trading_view_time_frame_converter.from_trading_view_time_frame(trading_view_time_frame),
                open_time=open_t,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                close_time=close_t
            ))

        return candles
