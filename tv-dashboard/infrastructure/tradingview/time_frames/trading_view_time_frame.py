from enum import Enum


class TradingViewTimeFrame(Enum):
    TF_1MIN = '1'
    TF_3MIN = '3'
    TF_5MIN = '5'
    TF_15MIN = '15'
    TF_1H = '60'
    TF_4H = '240'
    TF_8H = '480'
    TF_12H = '720'
    TF_1D = '1D'
    TF_1W = '1W'
    TF_1M = '1M'
    TF_1Y = '12M'

    def get_description(self) -> str:
        if self == TradingViewTimeFrame.TF_1MIN:
            return "1 min."
        if self == TradingViewTimeFrame.TF_3MIN:
            return "3 min."
        if self == TradingViewTimeFrame.TF_5MIN:
            return "5 min."
        if self == TradingViewTimeFrame.TF_15MIN:
            return "15 min."
        if self == TradingViewTimeFrame.TF_1H:
            return "1h"
        if self == TradingViewTimeFrame.TF_4H:
            return "4h"
        if self == TradingViewTimeFrame.TF_4H:
            return "8h"
        if self == TradingViewTimeFrame.TF_12H:
            return "12h"
        if self == TradingViewTimeFrame.TF_1D:
            return "daily"
        if self == TradingViewTimeFrame.TF_1W:
            return "weekly"
        if self == TradingViewTimeFrame.TF_1M:
            return "monthly"
        if self == TradingViewTimeFrame.TF_1Y:
            return "yearly"

    @staticmethod
    def from_string(tf_str: str) -> 'TradingViewTimeFrame':
        if TradingViewTimeFrame.TF_1MIN.value == tf_str:
            return TradingViewTimeFrame.TF_1MIN
        if TradingViewTimeFrame.TF_3MIN.value == tf_str:
            return TradingViewTimeFrame.TF_3MIN
        if TradingViewTimeFrame.TF_5MIN.value == tf_str:
            return TradingViewTimeFrame.TF_5MIN
        if TradingViewTimeFrame.TF_15MIN.value == tf_str:
            return TradingViewTimeFrame.TF_15MIN
        if TradingViewTimeFrame.TF_1H.value == tf_str:
            return TradingViewTimeFrame.TF_1H
        if TradingViewTimeFrame.TF_4H.value == tf_str:
            return TradingViewTimeFrame.TF_4H
        if TradingViewTimeFrame.TF_8H.value == tf_str:
            return TradingViewTimeFrame.TF_8H
        if TradingViewTimeFrame.TF_12H.value == tf_str:
            return TradingViewTimeFrame.TF_12H
        if TradingViewTimeFrame.TF_1D.value == tf_str:
            return TradingViewTimeFrame.TF_1D
        if TradingViewTimeFrame.TF_1W.value == tf_str:
            return TradingViewTimeFrame.TF_1W
        if TradingViewTimeFrame.TF_1M.value == tf_str:
            return TradingViewTimeFrame.TF_1M
        if TradingViewTimeFrame.TF_1Y.value == tf_str:
            return TradingViewTimeFrame.TF_1Y


ALL_TRADING_VIEW_TIME_FRAMES = [
    TradingViewTimeFrame.TF_1MIN,
    TradingViewTimeFrame.TF_3MIN,
    TradingViewTimeFrame.TF_5MIN,
    TradingViewTimeFrame.TF_15MIN,
    TradingViewTimeFrame.TF_1H,
    TradingViewTimeFrame.TF_4H,
    TradingViewTimeFrame.TF_12H,
    TradingViewTimeFrame.TF_1D,
    TradingViewTimeFrame.TF_1W,
    TradingViewTimeFrame.TF_1M,
    TradingViewTimeFrame.TF_1Y
]

PROFIT_CAP_COLORS = {
    TradingViewTimeFrame.TF_1MIN: 'rgba(255, 255, 255, 0.05)',
    TradingViewTimeFrame.TF_3MIN: 'rgba(233, 30, 99, 0.05)',
    TradingViewTimeFrame.TF_5MIN: 'rgba(255, 152, 0, 0.05)',
    TradingViewTimeFrame.TF_15MIN: 'rgba(76, 175, 80, 0.05)',
    TradingViewTimeFrame.TF_1H: 'rgba(0, 188, 212, 0.05)',
    TradingViewTimeFrame.TF_4H: 'rgba(255, 235, 59, 0.05)',
    TradingViewTimeFrame.TF_12H: 'rgba(41, 98, 255, 0.05)',
    TradingViewTimeFrame.TF_1D: 'rgba(242, 54, 69, 0.05)',
    TradingViewTimeFrame.TF_1W: 'rgba(156, 39, 176, 0.05)',
    TradingViewTimeFrame.TF_1M: 'rgba(149, 152, 161, 0.05)',
    TradingViewTimeFrame.TF_1Y: 'rgba(0, 255, 10, 1, 0.05)'
}

HOLD_LEVEL_LINE_COLORS = {
    TradingViewTimeFrame.TF_1MIN: 'rgba(255, 255, 255, 1)',
    TradingViewTimeFrame.TF_3MIN: 'rgba(233, 30, 99, 1)',
    TradingViewTimeFrame.TF_5MIN: 'rgba(255, 152, 0, 1)',
    TradingViewTimeFrame.TF_15MIN: 'rgba(76, 175, 80, 1)',
    TradingViewTimeFrame.TF_1H: 'rgba(0, 188, 212, 1)',
    TradingViewTimeFrame.TF_4H: 'rgba(255, 235, 59, 1)',
    TradingViewTimeFrame.TF_12H: 'rgba(41, 98, 255, 1)',
    TradingViewTimeFrame.TF_1D: 'rgba(242, 54, 69, 1)',
    TradingViewTimeFrame.TF_1W: 'rgba(156, 39, 176, 1)',
    TradingViewTimeFrame.TF_1M: 'rgba(149, 152, 161, 1)',
    TradingViewTimeFrame.TF_1Y: 'rgba(0, 255, 10, 1)'
}

PLANET_COLORS = {
    'Jupiter': 'rgba(255, 255, 255, 1)',
    'Sun': 'rgba(255, 152, 0, 1)',
    'Mars': 'rgba(233, 30, 99, 1)',
    'Moon': 'rgba(255, 152, 0, 1)',
    'Pluto': 'rgba(76, 175, 80, 1)',
    'Saturn': 'rgba(0, 188, 212, 1)',
    'Uranus': 'rgba(255, 235, 59, 1)',
    'Neptune': 'rgba(41, 98, 255, 1)',
    'Venus': 'rgba(14, 100, 179, 1)',
    'Mercury': 'rgba(240, 98, 146, 1)'
}

BREAK_LEVEL_LINE_COLORS = {
    TradingViewTimeFrame.TF_1MIN: 'rgba(67, 70, 81, 1)',
    TradingViewTimeFrame.TF_3MIN: 'rgba(67, 70, 81, 1)',
    TradingViewTimeFrame.TF_5MIN: 'rgba(0, 151, 167, 1)',
    TradingViewTimeFrame.TF_15MIN: 'rgba(5, 102, 86, 1)',
    TradingViewTimeFrame.TF_1H: 'rgba(251, 192, 45, 1)',
    TradingViewTimeFrame.TF_4H: 'rgba(230, 81, 0, 1)',
    TradingViewTimeFrame.TF_12H: 'rgba(12, 50, 153, 1)',
    TradingViewTimeFrame.TF_1D: 'rgba(128, 25, 34, 1)',
    TradingViewTimeFrame.TF_1W: 'rgba(74, 20, 140, 1)',
    TradingViewTimeFrame.TF_1M: 'rgba(149, 152, 161, 1)'
}

ALL_TV_TIME_FRAMES = [
    TradingViewTimeFrame.TF_1MIN,
    TradingViewTimeFrame.TF_3MIN,
    TradingViewTimeFrame.TF_5MIN,
    TradingViewTimeFrame.TF_15MIN,
    TradingViewTimeFrame.TF_1H,
    TradingViewTimeFrame.TF_4H,
    TradingViewTimeFrame.TF_12H,
    TradingViewTimeFrame.TF_1D,
    TradingViewTimeFrame.TF_1W,
    TradingViewTimeFrame.TF_1M,
    TradingViewTimeFrame.TF_1Y,
]
