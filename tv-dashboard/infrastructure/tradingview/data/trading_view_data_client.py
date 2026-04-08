import json
import os
import random
import string
import traceback
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import backoff
from websocket._core import create_connection

from domain.candles.candle import Candle
from domain.candles.candles import Candles
from domain.time_frames import TimeFrame, ALL_TIME_FRAMES
from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession
from infrastructure.tradingview.data.trading_view_api_datastream import DataStream
from infrastructure.tradingview.time_frames.time_frame_converter import TradingViewTimeFrameConverter


class TradingViewDataClient:
    def __init__(
            self,
            trading_view_time_frame_converter: TradingViewTimeFrameConverter,
            auto_refresh: bool = False,
            verbose: bool = True
    ):
        self.auto_refresh = auto_refresh
        self.trading_view_time_frame_converter = trading_view_time_frame_converter
        self.verbose = verbose

    @backoff.on_exception(backoff.expo, AttributeError, max_tries=20)
    def get_data(
            self,
            trading_view_session: TradingViewSession,
            ticker: str,
            time_frame: TimeFrame,
            bars_count: int = 5000
    ) -> List[Candle]:
        cache_path = os.path.join('cache', 'tickers')
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        ds = DataStream(trading_view_time_frame_converter=self.trading_view_time_frame_converter)
        session = self.generate_session()
        chart_session = self.generate_chart_session()

        headers = json.dumps({
            'Origin': 'https://data.tradingview.com'
        })
        ws = create_connection(
            'wss://prodata.tradingview.com/socket.io/websocket',
            headers=headers
        )
        ds.connect(
            ws=ws,
            trading_view_session=trading_view_session,
            ticker=ticker,
            trading_view_time_frame=self.trading_view_time_frame_converter.to_trading_view_time_frame(time_frame),
            chart_session=chart_session,
            session=session,
            bars_count=bars_count
        )

        try:
            candles = ds.get_candles(
                ws=ws,
                ticker=ticker,
                trading_view_time_frame=self.trading_view_time_frame_converter.to_trading_view_time_frame(time_frame),
                time_frame_relative_delta=TimeFrame.to_relativedelta(tf=time_frame)
            )
        except Exception as err:
            print(traceback.format_exc())
            print(err)
            raise err

        return candles

    def generate_session(self):
        string_length = 12
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for i in range(string_length))
        return "qs_" + random_string

    def generate_chart_session(self):
        string_length = 12
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for i in range(string_length))
        return "cs_" + random_string

    def load_all_data(
            self,
            trading_view_session: TradingViewSession,
            symbol: str,
            bars_count: int = 5000,
            time_frames = None,
            min_year: Optional[int] = None
    ) -> Candles:
        candles = Candles(
            time_frame=ALL_TIME_FRAMES[-1],
            candles=[],
            next_time_frame_candles=None
        )
        if time_frames is None:
            time_frames = list(reversed(ALL_TIME_FRAMES))

        current_candles = candles
        for i, time_frame in enumerate(time_frames):
            processes = []
            with ThreadPoolExecutor() as executor:
                processes.append(executor.submit(
                    self.load_data,
                    trading_view_session=trading_view_session,
                    symbol=symbol,
                    time_frame=time_frame,
                    bars_count=bars_count
                ))

            for job in futures.as_completed(processes):
                current_candles.candles = job.result()
                if min_year is not None:
                    current_candles = current_candles.apply_min_year(min_year=min_year)

                if i < len(time_frames) - 1:
                    current_candles.next_time_frame_candles = Candles(
                        time_frame=time_frames[i + 1],
                        candles=[],
                        next_time_frame_candles=None
                    )
                    current_candles = current_candles.next_time_frame_candles

        return candles

    def load_data(
            self,
            trading_view_session: TradingViewSession,
            symbol: str,
            time_frame: TimeFrame,
            bars_count: int = 5000
    ) -> List[Candle]:
        if self.verbose:
            print(f"Fetching data for {time_frame.value}, fetching last {bars_count} bars")

        return self.get_data(
            trading_view_session=trading_view_session,
            ticker=symbol,
            time_frame=time_frame,
            bars_count=bars_count
        )
