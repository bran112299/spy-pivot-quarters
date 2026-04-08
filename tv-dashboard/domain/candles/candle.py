import datetime
from dataclasses import dataclass
from typing import Tuple, Optional

from dataclasses_json import dataclass_json

from domain.time_frames import TimeFrame


@dataclass_json
@dataclass
class Candle:
    symbol: str
    open: float
    time_frame: TimeFrame
    open_time: datetime.datetime
    close: float
    close_time: datetime.datetime
    low: float
    high: float
    volume: float

    def is_same_color_candle(self, other: 'Candle') -> bool:
        return not self.is_opposite_color_candle(other)

    def is_opposite_color_candle(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return other.is_distribution_candle()
        return other.is_accumulation_candle()

    def confirms_level(self, is_accumulation: bool, level: float) -> bool:
        if is_accumulation:
            return self.close < level
        return self.close > level

    def hard_closes_level(self, level: float) -> bool:
        if self.is_accumulation_candle():
            return self.open > level
        return self.open < level

    def is_soft_hard_closed_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return other.open_time > self.open_time and \
                   other.open > self.low and \
                   other.close > self.low
        if self.is_distribution_candle():
            return other.open_time > self.open_time and \
                   other.open < self.high and \
                   other.close < self.high
        return False

    def is_body_soft_hard_closed_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return other.open_time > self.open_time and \
                   other.open > self.open and \
                   other.close > self.open
        if self.is_distribution_candle():
            return other.open_time > self.open_time and \
                   other.open < self.open and \
                   other.close < self.open
        return False

    def is_candle_wick_hold_price_hard_closed_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle() and other.is_accumulation_candle():
            return other.open > self.low
        if self.is_distribution_candle() and other.is_distribution_candle():
            return other.open < self.high
        return False

    def is_candle_body_hold_price_hard_closed_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle() and other.is_accumulation_candle():
            return other.open > self.open
        if self.is_distribution_candle() and other.is_distribution_candle():
            return other.open < self.open
        return False

    def is_wick_hard_closed_by(self, other: 'Candle') -> bool:
        if self.is_same_color_candle(other):
            return False

        if self.is_accumulation_candle():
            return other.high < self.low > other.close and other.is_distribution_candle()
        return other.low > self.high < other.close and other.is_accumulation_candle()

    def is_body_hard_closed_by(self, other: 'Candle') -> bool:
        if self.is_same_color_candle(other):
            return False

        if self.is_accumulation_candle():
            return other.high < self.open > other.close and other.is_distribution_candle()
        return other.low > self.open < other.close and other.is_accumulation_candle()

    def is_backward_hard_closed_by(self, other: 'Candle') -> bool:
        if self.is_opposite_color_candle(other):
            return False

        hold_level_price = self.get_hold_level_price()
        if self.is_accumulation_candle():
            return other.open > hold_level_price and other.low > hold_level_price
        return other.open < hold_level_price and other.high < hold_level_price

    def is_touched_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return other.high >= self.low
        return other.low <= self.high

    def is_body_touched_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return other.high >= self.open
        return other.low <= self.open

    def is_wick_tested_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return self.is_before(other) and other.high >= self.low
        return self.is_before(other) and other.low <= self.high

    def is_body_tested_by(self, other: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return self.is_before(other) and other.high >= self.open
        return self.is_before(other) and other.low <= self.open

    def is_backward_tested_by(self, other: 'Candle') -> bool:
        hold_level_price = self.get_hold_level_price()

        if self.is_accumulation_candle():
            return other.open > hold_level_price >= other.low and other.open > self.open

        return other.open < hold_level_price <= other.high and other.open < self.close

    def is_hold_level_for_current_price(self, current_price: float) -> bool:
        if self.is_accumulation_candle():
            return current_price < self.low
        return current_price > self.high

    def is_accumulation_candle(self) -> bool:
        return self.close > self.open

    def is_distribution_candle(self) -> bool:
        return self.close < self.open

    def is_reversal_bar_for(self, other: 'Candle') -> bool:
        is_reversal_bar = False
        if other.is_accumulation_candle() and self.is_distribution_candle():
            is_reversal_bar = self.low < other.low
        elif other.is_distribution_candle() and self.is_accumulation_candle():
            is_reversal_bar = self.high > other.high

        return is_reversal_bar

    def touches(self, price) -> bool:
        return self.high >= price >= self.low

    def touches_level(self, y) -> bool:
        if self.is_accumulation_candle():
            return self.high >= y
        return self.low <= y

    def is_internally_tested_by(self, testing_candle: 'Candle') -> Tuple[bool, bool]:
        return self.is_body_internally_tested_by(testing_candle), self.is_wick_internally_tested_by(testing_candle)

    def is_wick_internally_tested_by(self, testing_candle: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return (testing_candle.high >= self.low > testing_candle.open) or (testing_candle.high > self.low and testing_candle.is_accumulation_candle())
        return (testing_candle.low <= self.high < testing_candle.open) or (testing_candle.low < self.high and testing_candle.is_distribution_candle())

    def is_body_internally_tested_by(self, testing_candle: 'Candle') -> bool:
        if self.is_accumulation_candle():
            return (testing_candle.high >= self.open > testing_candle.open) or (testing_candle.high > self.open and testing_candle.is_accumulation_candle())
        return (testing_candle.low <= self.open < testing_candle.open) or (testing_candle.low < self.open and testing_candle.is_distribution_candle())

    def get_hold_level_price(self) -> float:
        if self.is_accumulation_candle():
            return self.low
        else:
            return self.high

    def get_origin_price(self):
        if self.is_accumulation_candle():
            return self.low
        return self.high

    def get_trend_reach_point(self):
        if self.is_accumulation_candle():
            return self.high
        return self.low

    def breaks_trend_from_base_point(self, base_point: 'Candle'):
        if base_point.is_accumulation_candle():
            return self.high > base_point.high
        return self.low < base_point.low

    def could_be_internally_tested_by(self, other: 'Candle') -> bool:
        if self.is_distribution_candle() and other.close < self.high < other.high:
            return True
        if self.is_accumulation_candle() and other.close > self.low > other.low:
            return True
        return False

    def is_before(self, other: 'Candle') -> bool:
        return self.open_time <= other.open_time

    def is_after(self, other: 'Candle') -> bool:
        return self.open_time >= other.open_time

    def opens_after(self, other: 'Candle') -> bool:
        return self.open_time > other.open_time

    def closes_after(self, other: 'Candle') -> bool:
        return self.close_time > other.close_time

    def is_above(self, other: Optional['Candle']) -> bool:
        if other is None:
            return True
        return self.low > other.low

    def is_below(self, other: Optional['Candle']) -> bool:
        if other is None:
            return True
        return self.high < other.high

    def is_closed_before(self, other: 'Candle') -> bool:
        return self.close_time < other.close_time

    def get_break_level_price(self):
        if self.is_accumulation_candle():
            return self.low
        return self.high

    def is_lower_time_frame_then(self, candle: 'Candle') -> bool:
        return TimeFrame.is_lower_time_frame_then(self.time_frame, candle.time_frame)

    def is_same_time_frame_then(self, candle: 'Candle') -> bool:
        return TimeFrame.is_same_time_frame_then(self.time_frame, candle.time_frame)

    def is_higher_time_frame_or_equal_then(self, candle: 'Candle') -> bool:
        return TimeFrame.is_higher_time_frame_or_equal_then(self.time_frame, candle.time_frame)

    def is_lower_time_frame_or_equal_then(self, candle: 'Candle') -> bool:
        return TimeFrame.is_lower_time_frame_or_equal_then(self.time_frame, candle.time_frame)

    def is_higher_time_frame_then(self, candle: 'Candle'):
        return TimeFrame.is_higher_time_frame_then(self.time_frame, candle.time_frame)

    def is_body_closed_by_same_color_candle(self, candle: 'Candle') -> bool:
        if not self.is_same_color_candle(candle):
            return False

        if self.is_accumulation_candle():
            return candle.low < self.low
        return candle.high > self.high

    def get_body_size(self) -> float:
        return abs(self.close - self.open)

    def get_candle_size(self) -> float:
        return abs(self.high - self.low)

    def is_dogi(self) -> bool:
        return self.open == self.close

    def is_inside(self, other: 'Candle') -> bool:
        return TimeFrame.is_lower_time_frame_or_equal_then(self.time_frame, other.time_frame) and \
               self.open_time >= other.open_time and self.close_time <= other.close_time

    def __contains__(self, item: 'Candle'):
        return self.close_time > item.open_time > self.open_time and \
               TimeFrame.is_higher_time_frame_then(self.time_frame, item.time_frame)

    def get_range(self):
        return self.high - self.low

    def is_completed(self):
        if self.close_time < self.open_time + TimeFrame.to_relativedelta(self.time_frame):
            return False
        return True

    def is_wicking_through_wick_of(self, candle: 'Candle') -> bool:
        if candle.is_distribution_candle():
            return self.high >= candle.high > self.close
        else:
            return self.low <= candle.low < self.close

    def is_wicking_through_body_of(self, candle: 'Candle') -> bool:
        if candle.is_distribution_candle():
            return self.high >= candle.open > self.close
        else:
            return self.low <= candle.open < self.close
