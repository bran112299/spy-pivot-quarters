from typing import Dict, List

from domain.candles.candle import Candle
from domain.trends.trend import Trend


class TradingViewTrendConverter:
    def get_trading_view_points_from_trend(self, trend: Trend) -> List[Dict]:
        base_point_candle = trend.refined_base_point_candle
        reach_point_candle = trend.refined_reach_point_candle

        return [
            self.get_trading_view_point_from_candle(base_point_candle),
            self.get_trading_view_point_from_candle(reach_point_candle),
        ]

    def get_trading_view_point_from_candle_and_price(self, candle: Candle, price: float) -> Dict:
        time_t = round(candle.open_time.timestamp())
        return {
            'price': price,
            'time_t': time_t,
            'offset': 0
        }

    def get_trading_view_point_from_candle(self, candle: Candle) -> Dict:
        if candle.is_accumulation_candle():
            price = candle.high
            time_t = round(candle.open_time.timestamp())
        else:
            price = candle.low
            time_t = round(candle.open_time.timestamp())

        return {
            'price': price,
            'time_t': time_t,
            'offset': 0
        }
