# from binance import Client

from domain.time_frames import TimeFrame
from infrastructure.tradingview.time_frames.trading_view_time_frame import TradingViewTimeFrame


class TradingViewTimeFrameConverter:
    def from_trading_view_time_frame(self, tv_tf: TradingViewTimeFrame) -> TimeFrame:
        if tv_tf == TradingViewTimeFrame.TF_1MIN:
            return TimeFrame.TF_1MINUTE

        if tv_tf == TradingViewTimeFrame.TF_3MIN:
            return TimeFrame.TF_3MINUTE

        if tv_tf == TradingViewTimeFrame.TF_5MIN:
            return TimeFrame.TF_5MINUTE

        if tv_tf == TradingViewTimeFrame.TF_15MIN:
            return TimeFrame.TF_15MINUTE

        if tv_tf == TradingViewTimeFrame.TF_1H:
            return TimeFrame.TF_1HOUR

        if tv_tf == TradingViewTimeFrame.TF_4H:
            return TimeFrame.TF_4HOUR

        if tv_tf == TradingViewTimeFrame.TF_8H:
            return TimeFrame.TF_8HOUR

        if tv_tf == TradingViewTimeFrame.TF_12H:
            return TimeFrame.TF_12HOUR

        if tv_tf == TradingViewTimeFrame.TF_1D:
            return TimeFrame.TF_1DAY

        if tv_tf == TradingViewTimeFrame.TF_1W:
            return TimeFrame.TF_1WEEK

        if tv_tf == TradingViewTimeFrame.TF_1M:
            return TimeFrame.TF_1MONTH

        if tv_tf == TradingViewTimeFrame.TF_1Y:
            return TimeFrame.TF_1YEAR

    def to_trading_view_time_frame(self, tf: TimeFrame) -> TradingViewTimeFrame:
        if tf == TimeFrame.TF_1MINUTE:
            return TradingViewTimeFrame.TF_1MIN

        if tf == TimeFrame.TF_3MINUTE:
            return TradingViewTimeFrame.TF_3MIN

        if tf == TimeFrame.TF_5MINUTE:
            return TradingViewTimeFrame.TF_5MIN

        if tf == TimeFrame.TF_15MINUTE:
            return TradingViewTimeFrame.TF_15MIN

        if tf == TimeFrame.TF_1HOUR:
            return TradingViewTimeFrame.TF_1H

        if tf == TimeFrame.TF_4HOUR:
            return TradingViewTimeFrame.TF_4H

        if tf == TimeFrame.TF_8HOUR:
            return TradingViewTimeFrame.TF_8H

        if tf == TimeFrame.TF_12HOUR:
            return TradingViewTimeFrame.TF_12H

        if tf == TimeFrame.TF_1DAY:
            return TradingViewTimeFrame.TF_1D

        if tf == TimeFrame.TF_1WEEK:
            return TradingViewTimeFrame.TF_1W

        if tf == TimeFrame.TF_1MONTH:
            return TradingViewTimeFrame.TF_1M

        if tf == TimeFrame.TF_1YEAR:
            return TradingViewTimeFrame.TF_1Y

    def from_binance_kline_interval(self, kline_interval: str) -> TradingViewTimeFrame:
        if kline_interval == Client.KLINE_INTERVAL_1MINUTE:
            return TradingViewTimeFrame.TF_1MINUTE

        if kline_interval == Client.KLINE_INTERVAL_3MINUTE:
            return TradingViewTimeFrame.TF_3MINUTE

        if kline_interval == Client.KLINE_INTERVAL_5MINUTE:
            return TradingViewTimeFrame.TF_5MINUTE

        if kline_interval == Client.KLINE_INTERVAL_15MINUTE:
            return TradingViewTimeFrame.TF_15MINUTE

        if kline_interval == Client.KLINE_INTERVAL_30MINUTE:
            return TradingViewTimeFrame.TF_30MINUTE

        if kline_interval == Client.KLINE_INTERVAL_1HOUR:
            return TradingViewTimeFrame.TF_1HOUR

        if kline_interval == Client.KLINE_INTERVAL_4HOUR:
            return TradingViewTimeFrame.TF_4HOUR

        if kline_interval == Client.KLINE_INTERVAL_6HOUR:
            return TradingViewTimeFrame.TF_6HOUR

        if kline_interval == Client.KLINE_INTERVAL_8HOUR:
            return TradingViewTimeFrame.TF_8HOUR

        if kline_interval == Client.KLINE_INTERVAL_12HOUR:
            return TradingViewTimeFrame.TF_12HOUR

        if kline_interval == Client.KLINE_INTERVAL_1DAY:
            return TradingViewTimeFrame.TF_1DAY

        if kline_interval == Client.KLINE_INTERVAL_3DAY:
            return TradingViewTimeFrame.TF_3DAY

        if kline_interval == Client.KLINE_INTERVAL_1WEEK:
            return TradingViewTimeFrame.TF_1WEEK

        if kline_interval == Client.KLINE_INTERVAL_1MONTH:
            return TradingViewTimeFrame.TF_1MONTH
