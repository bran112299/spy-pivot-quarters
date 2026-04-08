import datetime
from dataclasses import dataclass
from typing import Tuple, Optional, List

from domain.candles.candle import Candle
from domain.time_frames import TimeFrame


@dataclass
class Trend:
    base_point: Tuple[int, Candle]
    reach_point: Tuple[int, Candle]
    refined_base_point_candle: Candle
    refined_reach_point_candle: Candle
    trend_break_candle: Optional[Candle] = None
    exterior_trend: Optional['Trend'] = None
    is_massaged: bool = False
    n_massaged: int = 0
    touches: List[Candle] = None
    trend_allowances: List[Tuple[Candle, TimeFrame]] = None
    adaptations: List[Candle] = None
    soft_hard_close_candle: Optional[Candle] = None

    def get_line_width(self) -> int:
        if self.trend_allowances is None:
            return 1
        n_allowances = len(self.trend_allowances)
        if n_allowances > 4:
            return 4
        return n_allowances

    def set_trend_break_candle(self, candle: Candle):
        self.trend_break_candle = candle

    def set_reach_point(self, i: int, candle: Candle, refined_reach_point_candle: Candle):
        self.reach_point = (i, candle)
        self.touches = []
        if self.adaptations is None:
            self.adaptations = []
        self.adaptations.append(candle)
        self.refined_reach_point_candle = refined_reach_point_candle

    def get_time_frame(self) -> TimeFrame:
        return self.base_point[1].time_frame

    def get_base_point_index(self) -> int:
        return self.base_point[0]

    def get_reach_point_index(self) -> int:
        return self.reach_point[0]

    def get_base_point_candle(self) -> Candle:
        return self.base_point[1]

    def get_base_point_price(self) -> float:
        if self.is_uptrend():
            return self.base_point[1].low
        return self.base_point[1].high

    def get_reach_point_price(self) -> float:
        if self.is_uptrend():
            return self.reach_point[1].low
        return self.reach_point[1].high

    def get_base_point_open_time(self) -> datetime.datetime:
        return self.base_point[1].open_time

    def get_reach_point_candle(self) -> Candle:
        return self.reach_point[1]

    def get_reach_point_time(self) -> datetime.datetime:
        return self.reach_point[1].open_time

    def get_trend_value_at_x(self, x: float) -> float:
        m = self.get_slope()
        b = self.get_base_point_candle().get_trend_reach_point()

        return (m * x) + b

    def get_slope(self) -> float:
        return self.calculate_slope(
            self.get_base_point_x_y(),
            self.get_reach_point_x_y()
        )

    def get_base_point_x_y(self):
        return self.base_point[0], self.get_base_point_candle().get_trend_reach_point()

    def get_reach_point_x_y(self):
        return self.reach_point[0], self.get_reach_point_candle().get_trend_reach_point()

    def calculate_slope(self, point_one, point_two):
        (x1, y1) = point_one
        (x2, y2) = point_two
        s = (y2 - y1) / (x2 - x1)

        return s

    def is_valid(self) -> bool:
        if self.touches is None:
            return False
        enough_touches = len(self.touches) >= 3
        if not enough_touches:
            return False

        base_point_candle = self.get_base_point_candle()
        reach_point_candle = self.get_reach_point_candle()

        if self.trend_break_candle is not None:
            return False

        if not base_point_candle.is_same_color_candle(reach_point_candle):
            return False

        if base_point_candle.is_after(reach_point_candle):
            return False

        if base_point_candle.is_distribution_candle():
            if reach_point_candle.low < base_point_candle.low:
                return False
        if base_point_candle.is_accumulation_candle():
            if reach_point_candle.high > base_point_candle.high:
                return False

        if self.exterior_trend is not None and not self.is_inside(self.exterior_trend):
            return False

        return True

    def is_downtrend(self) -> bool:
        return not self.is_uptrend()

    def is_uptrend(self) -> bool:
        return self.get_reach_point_candle().close > self.get_base_point_candle().close

    def is_massaged_from(self, trend) -> bool:
        return self.n_massaged > trend.n_massaged

    def is_started_inside(self, other: 'Trend') -> bool:
        base_point = self.get_base_point_candle()
        y = other.calculate_trend_value_for_candle(base_point)

        if base_point.is_distribution_candle():
            return base_point.low > y

        return base_point.high < y

    def is_inside(self, other: 'Trend') -> bool:
        if self.get_base_point_candle().is_inside(other.get_base_point_candle()) and \
                self.get_base_point_price() == other.get_base_point_price():
            return False
        return self.is_steeper(other)

    def is_steeper(self, other: 'Trend') -> bool:
        if self.is_uptrend():
            return self.get_timestamp_slope() > other.get_timestamp_slope()
        else:
            return self.get_timestamp_slope() < other.get_timestamp_slope()

    def get_distance_from(self, candle: Candle, for_reach_point_price: bool = True) -> float:
        y = self.calculate_trend_value_for_candle(candle)
        candle_reach_point_price = candle.get_trend_reach_point()
        if not for_reach_point_price:
            if self.is_uptrend():
                candle_reach_point_price = candle.low
            else:
                candle_reach_point_price = candle.high

        if self.is_uptrend():
            return y - candle_reach_point_price

        return candle_reach_point_price - y

    def get_timestamp_slope(self) -> float:
        reach_point_x = self.refined_reach_point_candle.open_time.timestamp() - \
                        self.refined_base_point_candle.open_time.timestamp()
        base_point_price = self.base_point[1].get_trend_reach_point()
        reach_point_price = self.reach_point[1].get_trend_reach_point()

        return self.calculate_slope(
            point_one=(0, base_point_price),
            point_two=(reach_point_x, reach_point_price),
        )

    def calculate_trend_value_for_candle(self, candle: Candle) -> float:
        m = self.get_timestamp_slope()
        b = self.get_base_point_candle().get_trend_reach_point()
        candle_x = candle.open_time.timestamp() - self.base_point[1].open_time.timestamp()

        return (m * candle_x) + b

    def is_touched_by(self, candle: Candle):
        return self.get_distance_from(candle, for_reach_point_price=False) >= 0

    def add_touch(self, candle: Candle):
        if self.touches is None:
            self.touches = []

        return self.touches.append(candle)

    def add_trend_allowance(self, base_point: Candle, time_frame: TimeFrame):
        if self.trend_allowances is None:
            self.trend_allowances = []
        self.trend_allowances.append((base_point, time_frame))

    def has_n_touches(self, n_touches: int) -> bool:
        if self.touches is None:
            return False
        return len(self.touches) >= n_touches

    def get_adaptations_after(self, after: Candle) -> List[Candle]:
        if self.adaptations is None or len(self.adaptations) == 0:
            return []

        return [a for a in self.adaptations if a.open_time > after.open_time]

    def is_inside_a_higher_time_frame_trend_with_same_base_point(self, trends: List['Trend']) -> bool:
        for other_trend in trends:
            base_point_candle = self.get_base_point_candle()
            other_base_point = other_trend.get_base_point_candle()
            base_point_inside = base_point_candle.is_inside(other_base_point)
            if self.is_lower_time_frame_then(other_trend) and base_point_inside:
                return True

        return False

    def is_inside_a_trend_with_less_touches(self, trends: List['Trend']) -> bool:
        is_inside_a_trend_with_less_touches: bool = False
        for other_trend in trends:
            if other_trend.get_base_point_open_time() < self.get_base_point_open_time() and \
                    len(other_trend.touches) > len(self.touches):
                is_inside_a_trend_with_less_touches = True

        return is_inside_a_trend_with_less_touches

    def is_same_time_frame_as(self, other_trend: 'Trend') -> bool:
        return TimeFrame.is_same_time_frame_then(
            tf=self.get_time_frame(),
            other_tf=other_trend.get_time_frame()
        )

    def is_lower_time_frame_then(self, other_trend: 'Trend') -> bool:
        return TimeFrame.is_lower_time_frame_then(
            tf=self.get_time_frame(),
            other_tf=other_trend.get_time_frame()
        )

    def is_lower_time_frame_or_equal_then(self, other_trend: 'Trend') -> bool:
        return TimeFrame.is_lower_time_frame_or_equal_then(
            tf=self.get_time_frame(),
            other_tf=other_trend.get_time_frame()
        )

    def is_reach_point_before(self, other_trend: 'Trend') -> bool:
        reach_point_candle = self.get_reach_point_candle()
        other_reach_point = other_trend.get_reach_point_candle()
        return reach_point_candle.is_before(other=other_reach_point)

    def is_reach_point_before_candle(self, candle: 'Candle') -> bool:
        reach_point_candle = self.get_reach_point_candle()
        return reach_point_candle.is_before(other=candle)

    def is_base_point_before(self, other: 'Trend') -> bool:
        base_point_candle = self.get_base_point_candle()
        other_base_point = other.get_base_point_candle()
        return base_point_candle.is_before(other=other_base_point)

    def is_base_point_before_candle(self, candle: 'Candle') -> bool:
        base_point_candle = self.get_base_point_candle()
        return base_point_candle.is_before(other=candle)

    def is_base_point_after(self, other: 'Trend') -> bool:
        base_point_candle = self.get_base_point_candle()
        other_base_point = other.get_base_point_candle()
        return base_point_candle.is_after(other=other_base_point)

    def set_soft_hard_close_candle(self, candle: Optional['Candle'] = None):
        self.soft_hard_close_candle = candle

    def is_soft_hard_closed(self):
        return self.soft_hard_close_candle is not None
