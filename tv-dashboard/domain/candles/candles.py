import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

from domain.candles.candle import Candle
from domain.time_frames import TimeFrame


@dataclass
class Candles:
    time_frame: TimeFrame
    candles: List[Candle]
    next_time_frame_candles: Optional['Candles']

    def get_candles(self) -> List[Candle]:
        return self.candles

    def get_symbol(self) -> str:
        return self.candles[0].symbol.replace(':', '-')

    def get_end_date(self) -> datetime.date:
        if self.next_time_frame_candles.next_time_frame_candles is not None:
            return self.next_time_frame_candles.get_end_date()
        return self[-1].open_time.date()

    def get_all_distribution_candles_index_tuple(
            self,
            after: Candle = None,
            min_price: float = None,
            remove_non_completed_candles: bool = False
    ) -> List[Tuple[int, Candle]]:
        candles = []
        for i, c in enumerate(self.candles):
            if c.is_distribution_candle():
                if len(candles) == 0:
                    candles.append((i, c))
                elif i > candles[-1][0]:
                    candles.append((i, c))
        if min_price is not None:
            candles = [c for c in candles if c[1].low >= min_price]

        if after is not None:
            candles = [c for c in candles if c[1].is_after(after)]

        if remove_non_completed_candles:
            candles = [
                (i, c) for i, c in candles
                if c.is_completed() and i < len(self) - 1
            ]

        return candles

    def get_all_accumulation_candles_index_tuple(
            self,
            after: Candle,
            max_price: float = None,
            remove_non_completed_candles: bool = False
    ) -> List[Tuple[int, Candle]]:
        candles = []
        for i, c in enumerate(self.candles):
            if c.is_accumulation_candle():
                if len(candles) == 0:
                    candles.append((i, c))
                elif i > candles[-1][0]:
                    candles.append((i, c))
        if max_price is not None:
            candles = [c for c in candles if c[1].high <= max_price]

        if after is not None:
            candles = [c for c in candles if c[1].is_after(after)]

        if remove_non_completed_candles:
            max_index = len(self) - 1
            candles = [
                (i, c) for i, c in candles
                if c.is_completed() and i < max_index
            ]

        return candles

    def get_accumulation_max_hard_close_prices(self):
        max_hard_closing_prices = []
        for i, _ in enumerate(self[:-1]):
            max_hard_closing_price = None
            for j, c in enumerate(self[i + 1:]):
                if max_hard_closing_price is None and c.is_accumulation_candle():
                    max_hard_closing_price = c.low
                elif max_hard_closing_price is not None and c.is_accumulation_candle():
                    if c.low > max_hard_closing_price:
                        max_hard_closing_price = c.low
            max_hard_closing_prices.append(max_hard_closing_price)
        max_hard_closing_prices.append(None)
        return max_hard_closing_prices

    def get_current_price(self) -> float:
        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.get_current_price()
        return self.candles[-1].close

    def is_wick_internally_tested_by(self, candle: Candle, testing_candle: Candle) -> bool:
        internal_candles: List[Candle] = self.get_candles_inside(testing_candle)
        for c in internal_candles:
            if candle.is_wick_tested_by(c):
                return True
        return False

    def is_body_internally_tested_by(self, candle: Candle, testing_candle: Candle) -> bool:
        internal_candles: List[Candle] = self.get_candles_inside(testing_candle)
        for c in internal_candles:
            if candle.is_body_internally_tested_by(c):
                return True
        return False

    # Same as get_candles_between?
    def get_candles_inside(self, candle: Candle) -> List[Candle]:
        candles_inside = []
        for c in self.candles:
            if c.open_time >= candle.open_time and c.close_time <= candle.close_time:
                candles_inside.append(c)
        return candles_inside

    def filter_candles_by_index(self, distribution_candle_index_tuples: List[Tuple[int, Candle]]):
        previous_i = None
        new_candles = []
        for i, c in distribution_candle_index_tuples:
            if previous_i is None or i > previous_i:
                previous_i = i
                new_candles.append((i, c))

        return new_candles

    def could_become_a_frontside(self, index: int) -> bool:
        if self[index].is_dogi():
            return False

        second_next_candle_hard_closes = self[index + 2].confirms_level(
            level=self[index].get_hold_level_price(),
            is_accumulation=self[index].is_accumulation_candle()
        ) if len(self) > index + 2 else False

        follow_by_two_opposite_color_candles = self.is_candle_followed_by_n_opposite_color_candles(
            index_candle=index,
            n_candles=2
        )
        second_next_is_same_color = self[index + 2].is_same_color_candle(self[index])

        return follow_by_two_opposite_color_candles or \
               (second_next_candle_hard_closes and second_next_is_same_color)

    def is_frontside_internally_tested(
            self,
            index_hold: int,
            index_body_hard_close: Optional[int],
            index_wick_hard_close: Optional[int]
    ) -> Tuple[bool, bool]:
        body_internally_tested = self.is_body_internally_tested(index_hold, index_body_hard_close)
        wick_internally_tested = self.is_wick_internally_tested(index_hold, index_wick_hard_close)

        return body_internally_tested, wick_internally_tested

    def is_body_internally_tested(self, index_hold: int, index_hard_close: Optional[int]):
        if index_hard_close is None:
            return False

        body_internally_tested = False

        for i in range(index_hold + 1, index_hard_close):
            body_internally_tested = self[index_hold].is_body_internally_tested_by(self[i])
            if body_internally_tested:
                return True

        return body_internally_tested

    def is_wick_internally_tested(self, index_hold: int, index_hard_close: Optional[int]):
        if index_hard_close is None:
            return False

        wick_internally_tested = False

        for i in range(index_hold + 1, index_hard_close):

            wick_internally_tested = self[index_hold].is_wick_internally_tested_by(self[i])
            if wick_internally_tested:
                return True

        return wick_internally_tested

    def is_backside_internally_tested(
            self,
            index_hold: int,
            index_body_hard_close: Optional[int],
            index_wick_hard_close: Optional[int]
    ) -> Tuple[bool, bool]:
        wick_wicked_through = self.is_wick_wicked_through_before_confirmation(
            index_hold=index_hold,
            index_hard_close=index_wick_hard_close,
            max_same_color_wick_through_count=3,
            max_opposite_color_wick_through_count=0
        )
        body_wicked_through = self.is_body_wicked_through_before_confirmation(
            index_hold=index_hold,
            index_hard_close=index_body_hard_close,
            max_same_color_wick_through_count=3,
            max_opposite_color_wick_through_count=0
        )

        wick_tested_by_confirmation = False
        if index_wick_hard_close is not None:
            wick_tested_by_confirmation = self[index_hold].is_wick_internally_tested_by(self[index_wick_hard_close])

        body_tested_by_confirmation = False
        if index_body_hard_close is not None:
            body_tested_by_confirmation = self[index_hold].is_body_internally_tested_by(self[index_body_hard_close])

        wick_internally_tested = wick_wicked_through or wick_tested_by_confirmation
        body_internally_tested = body_wicked_through or body_tested_by_confirmation

        return body_internally_tested, wick_internally_tested

    def is_wick_wicked_through_before_confirmation(
            self,
            index_hold: int,
            index_hard_close: Optional[int],
            max_same_color_wick_through_count: int,
            max_opposite_color_wick_through_count: int
    ) -> bool:
        if index_hard_close is None:
            return False

        hold_candle = self[index_hold]
        opposite_color_wick_through_count = 0
        same_color_wick_through_count = 0
        for wicking_candle in self[index_hold + 1: index_hard_close]:
            if wicking_candle.is_wicking_through_wick_of(hold_candle):
                if hold_candle.is_same_color_candle(wicking_candle):
                    same_color_wick_through_count += 1
                else:
                    opposite_color_wick_through_count += 1

        return same_color_wick_through_count > max_same_color_wick_through_count or \
               opposite_color_wick_through_count > max_opposite_color_wick_through_count

    def is_body_wicked_through_before_confirmation(
            self,
            index_hold: int,
            index_hard_close: Optional[int],
            max_same_color_wick_through_count: int,
            max_opposite_color_wick_through_count: int
    ) -> bool:
        if index_hard_close is None:
            return False

        hold_candle = self[index_hold]
        opposite_color_wick_through_count = 0
        same_color_wick_through_count = 0
        for wicking_candle in self[index_hold + 1: index_hard_close]:
            if wicking_candle.is_wicking_through_body_of(hold_candle):
                if hold_candle.is_same_color_candle(wicking_candle):
                    same_color_wick_through_count += 1
                else:
                    opposite_color_wick_through_count += 1

        return same_color_wick_through_count > max_same_color_wick_through_count or \
               opposite_color_wick_through_count > max_opposite_color_wick_through_count

    def is_valid_frontside_at_index(
            self,
            index: int,
            index_body_hard_close: Optional[int],
            index_wick_hard_close: Optional[int]
    ) -> Tuple[bool, bool]:
        body_internally_tested, wick_internally_tested = self.is_frontside_internally_tested(
            index_hold=index,
            index_body_hard_close=index_body_hard_close,
            index_wick_hard_close=index_wick_hard_close
        )

        return not body_internally_tested, not wick_internally_tested

    def is_tested_in_range(self, index: int, index_hard_close: int) -> bool:
        start = index + 1
        end = index_hard_close
        for i in range(start, end):
            if self[i].is_same_color_candle(self[index]) and \
                    (self[index].is_wick_tested_by(self[i]) or
                     self[i].is_same_color_candle(self[index]) and
                     self[index].is_accumulation_candle() and self[i].high >= self[index].get_hold_level_price() or
                     self[index].is_distribution_candle() and self[i].low <= self[index].get_hold_level_price()):
                return True
        return False

    def could_become_a_backside(self, index: int) -> bool:
        if self[index].is_dogi():
            return False

        return self[index].is_opposite_color_candle(self[index - 1]) and \
               self.is_candle_followed_by_n_same_color_candles(index_candle=index, n_candles=1)

    def is_valid_backside_at_index(self, index: int, index_hard_close: Optional[int]) -> bool:
        if index_hard_close is None:
            return False

        # closed_by_same_color_candle_before_hard_close = self.is_candle_body_closed_by_same_color_candle_before(
        #     index_candle=index,
        #     index_end=index_hard_close
        # )
        #
        is_not_bs_internally_tested_before_formation = not self.is_bs_internally_tested_before_formation(
            index_candle=index,
            index_end=index_hard_close
        )

        after_opposite_candle_color = self[index].is_opposite_color_candle(self[index - 1])
        body_not_internally_tested = not self[index].is_body_internally_tested_by(self[index_hard_close])
        wick_not_internally_tested = not self[index].is_wick_internally_tested_by(self[index_hard_close])

        return index_hard_close is not None and \
               after_opposite_candle_color and \
               is_not_bs_internally_tested_before_formation and \
               (body_not_internally_tested or wick_not_internally_tested)

    def get_deepest_opposite_color_candle_in_range(
            self,
            index_candle: int,
            index_start: int,
            index_end: int
    ) -> Candle:
        is_distribution_hold_level = self.candles[index_candle].is_distribution_candle()
        is_accumulation_hold_level = self.candles[index_candle].is_accumulation_candle()

        deepest_opposite_color_candle: Optional[Candle] = None
        for potential_break in self.candles[index_start:index_end]:
            if is_distribution_hold_level:
                is_new_deepest_opposite_color_candle = deepest_opposite_color_candle is None or \
                                                       potential_break.get_break_level_price() < \
                                                       deepest_opposite_color_candle.get_break_level_price()
                if potential_break.is_accumulation_candle() and is_new_deepest_opposite_color_candle:
                    deepest_opposite_color_candle = potential_break
            if is_accumulation_hold_level:
                is_new_deepest_opposite_color_candle = deepest_opposite_color_candle is None or \
                                                       potential_break.get_break_level_price() > \
                                                       deepest_opposite_color_candle.get_break_level_price()
                if potential_break.is_distribution_candle() and is_new_deepest_opposite_color_candle:
                    deepest_opposite_color_candle = potential_break

        return deepest_opposite_color_candle

    def is_candle_followed_by_n_same_color_candles(self, index_candle: int, n_candles: int) -> bool:
        candle = self.candles[index_candle]
        for i in range(index_candle + 1, index_candle + n_candles + 1):
            if candle.is_opposite_color_candle(self.candles[i]):
                return False
        return True

    def is_candle_followed_by_n_opposite_color_candles(self, index_candle: int, n_candles: int) -> bool:
        candle = self.candles[index_candle]
        for i in range(1, n_candles + 1):
            if candle.is_same_color_candle(self.candles[index_candle + i]):
                return False
        return True

    def is_candle_body_closed_by_same_color_candle_before(self, index_candle: int, index_end: int) -> bool:
        for i in range(index_candle + 1, index_end):
            if self[index_candle].is_body_closed_by_same_color_candle(self[i]):
                return True
        return False

    def is_bs_internally_tested_before_formation(self, index_candle: int, index_end: int) -> bool:
        candle = self.candles[index_candle]
        for i in range(index_candle + 1, index_end):
            other = self[i]
            if candle.is_accumulation_candle():
                val = self[index_candle].low
                if (other.high > val > other.open) or \
                        (other.low < val < other.close and other.is_distribution_candle()):
                    return True
            else:
                val = self[index_candle].high
                if (other.low < val < other.open) or \
                        (other.high > val > other.close and other.is_accumulation_candle()):
                    return True
        return False

    def get_candle_hard_close_index(
            self,
            index_candle: int,
            index_start_for_hard_close: int
    ) -> Tuple[Optional[int], Optional[int]]:
        candle = self.candles[index_candle]
        wick_index = None
        body_index = None

        for i in range(index_start_for_hard_close, len(self)):
            other_candle = self.candles[i]
            if candle.is_wick_hard_closed_by(other_candle):
                wick_index = i
                break

        for i in range(index_start_for_hard_close, len(self)):
            other_candle = self.candles[i]
            if candle.is_body_hard_closed_by(other_candle):
                body_index = i
                break

        return wick_index, body_index

    def is_wick_internally_tested_on_a_lower_time_frame_by(
            self,
            candle: Candle,
            testing_candle: Optional[Candle]
    ) -> bool:
        if testing_candle is None:
            return False

        return candle.could_be_internally_tested_by(testing_candle) and \
               self.next_time_frame_candles is not None and \
               self.next_time_frame_candles.is_wick_internally_tested_by(candle, testing_candle)

    def is_body_internally_tested_on_a_lower_time_frame_by(
            self,
            candle: Candle,
            testing_candle: Optional[Candle]
    ) -> bool:
        if testing_candle is None:
            return False

        return candle.could_be_internally_tested_by(testing_candle) and \
               self.next_time_frame_candles is not None and \
               self.next_time_frame_candles.is_body_internally_tested_by(candle, testing_candle)

    def is_candle_tested_at_or_after_index(self, candle: Candle, index: int) -> bool:
        for y in range(index, len(self)):
            if candle.is_wick_tested_by(self[y]):
                return True

        return False

    def is_true_frontside(self, index_candle: int) -> bool:
        candle: Candle = self[index_candle]
        next_candle: Candle = self[index_candle + 1]

        return next_candle.get_body_size() > candle.get_body_size()

    def on_candles(self, candles: List[Candle]):
        pass

    def for_time_frame(self, time_frame: TimeFrame) -> 'Candles':
        if self.time_frame == time_frame:
            return self
        return self.next_time_frame_candles.for_time_frame(time_frame)

    def get_candles_after(self, after_datetime: datetime.datetime) -> 'Candles':
        candles = [candle for candle in self.candles if candle.open_time >= after_datetime]
        return Candles(
            time_frame=self.time_frame,
            candles=candles,
            next_time_frame_candles=None
        )

    def get_candles_after_for_timeframe(self, after_datetime: datetime.datetime, time_frame) -> 'Candles':
        if self.time_frame != time_frame:
            if self.next_time_frame_candles is not None:
                return self.next_time_frame_candles.get_candles_after_for_timeframe(after_datetime, time_frame)
        else:
            candles = [candle for candle in self.candles if candle.open_time >= after_datetime]
            return Candles(
                time_frame=time_frame,
                candles=candles,
                next_time_frame_candles=None
            )

    def get_min_price(self) -> float:
        return min([c.low for c in self])

    def get_max_price(self) -> float:
        return min([c.high for c in self])

    @staticmethod
    def from_json(json_dict: Dict) -> 'Candles':
        return Candles(
            time_frame=TimeFrame(json_dict['time_frame']),
            candles=[Candle.from_json(c) for c in json_dict['candles']],
            next_time_frame_candles=Candles.from_json(json_dict['next_time_frame_candles'])
            if json_dict['next_time_frame_candles'] is not None else None
        )

    def to_json(self):
        next_time_frame_json = self.next_time_frame_candles.to_json() if self.next_time_frame_candles is not None \
            else None

        return {
            'time_frame': self.time_frame.value,
            'candles': [c.to_json() for c in self],
            'next_time_frame_candles': next_time_frame_json
        }

    def get_previous_distance_for_time_frame(
            self,
            time_frame: TimeFrame,
            entry_candle: Candle
    ) -> float:
        if self.time_frame == time_frame:
            first_candle_before = self.get_first_candle_before(candle=entry_candle)
            return first_candle_before.get_range()

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.get_previous_distance_for_time_frame(
                time_frame=time_frame,
                entry_candle=entry_candle
            )

        return self[-2].get_range()

    def get_first_candle_before(self, candle: 'Candle') -> Candle:
        previous_candle = self[0]
        for c in self:
            if c.open_time > candle.open_time:
                return previous_candle
            previous_candle = c
        return previous_candle

    def get_lowest_time_frame_entry_candle(self, is_long: bool, entry_candle: Candle, entry_price: float) -> \
            Optional[Candle]:
        if self.next_time_frame_candles is not None:
            lower_tf_entry_candle = self.next_time_frame_candles.get_lowest_time_frame_entry_candle(
                is_long=is_long,
                entry_candle=entry_candle,
                entry_price=entry_price
            )
            if lower_tf_entry_candle is not None:
                return lower_tf_entry_candle

        for candle in self:
            if candle.open_time > entry_candle.open_time and candle.close_time < entry_candle.close_time:
                if is_long:
                    if candle.low <= entry_price:
                        return candle
                else:
                    if candle.high >= entry_price:
                        return candle

        return None

    def find_candle_by_high(self, high_price: float) -> Candle:
        for c in self:
            if float(c.high) == float(high_price):
                return c
        raise Exception('candle not found')

    def find_candle_by_low(self, low_price: float) -> Candle:
        for c in self:
            if float(c.low) == float(low_price):
                return c
        raise Exception('candle not found')

    def find_candle_by_open(self, open_price: float) -> Candle:
        for c in self:
            if c.open == open_price:
                return c
        raise Exception('candle not found')

    def find_candle_by_exceeded(self, price: float, time_frame, over=False) -> Candle:
        for c in self:
            if over:
                if c.high >= price:
                    return c
            else:
                if c.low <= price:
                    return c

    def get_min_time(self):
        return self[0].open_time

    def get_max_time(self):
        return self[-1].close_time

    def get_first_candle_outside_of_range_before(
            self,
            before: datetime.datetime,
            range_distance: float
    ) -> Optional[Candle]:
        if self.next_time_frame_candles is not None:
            lower_tf_candle = self.next_time_frame_candles.get_first_candle_outside_of_range_before(
                before=before,
                range_distance=range_distance
            )

            if lower_tf_candle is not None:
                return lower_tf_candle

        candles = list(reversed([c for c in self if c.open_time < before]))
        if len(candles) == 0:
            return None

        top_range = candles[0].close + range_distance
        bottom_range = candles[0].close - range_distance
        for c in candles:
            if c.low < bottom_range:
                return c
            if c.high > top_range:
                return c

        return None

    def is_target_reached_after_on_time_frame(
            self,
            target_price,
            after: datetime.datetime,
            time_frame: TimeFrame,
            is_long: bool
    ):
        if self.time_frame != time_frame:
            if self.next_time_frame_candles is not None:
                return self.next_time_frame_candles.is_target_reached_after_on_time_frame(
                    target_price=target_price,
                    after=after,
                    time_frame=time_frame,
                    is_long=is_long
                )
            return False

        for c in self:
            if c.open_time >= after:
                if is_long and c.high >= target_price:
                    return True
                if not is_long and c.low <= target_price:
                    return True

        return False

    def is_target_reached_after(
            self,
            target_price,
            after: datetime.datetime,
            is_long: bool
    ):
        is_target_reached = False
        for c in self:
            if c.open_time >= after:
                if is_long and c.high >= target_price:
                    is_target_reached = True
                if not is_long and c.low <= target_price:
                    is_target_reached = True

        if self.next_time_frame_candles is not None:
            is_target_reached = is_target_reached or self.next_time_frame_candles.is_target_reached_after(
                target_price=target_price,
                after=after,
                is_long=is_long
            )

        return is_target_reached

    def remove_all_candles_from_time_frame(self, time_frame: TimeFrame):
        if self.next_time_frame_candles.time_frame == time_frame:
            self.next_time_frame_candles = None
        elif self.next_time_frame_candles is not None:
            self.next_time_frame_candles.remove_all_candles_from_time_frame(time_frame)

    def get_all_time_frames(self, time_frames: List[TimeFrame] = None) -> List[TimeFrame]:
        if time_frames is None:
            time_frames = []
        time_frames.append(self.time_frame)

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.get_all_time_frames(time_frames)

        return time_frames

    def get_time_frame_candles(self, time_frame: TimeFrame) -> List[Candle]:
        if self.time_frame == time_frame:
            return self.candles
        else:
            return self.next_time_frame_candles.get_time_frame_candles(time_frame)

    def find_candle_that_contains(self, candle: Candle) -> Candle:
        for other_candle in self:
            if candle in other_candle:
                return other_candle
        raise Exception('not found')

    def trim_candles(self, max_candles_count: int, trim_next_time_frame_candles: bool) -> 'Candles':
        candles = self.candles
        if len(self) > max_candles_count:
            candles = self.candles[-max_candles_count:]

        next_candles = self.next_time_frame_candles
        if self.next_time_frame_candles is not None and trim_next_time_frame_candles:
            next_candles = self.next_time_frame_candles.trim_candles(
                max_candles_count=max_candles_count,
                trim_next_time_frame_candles=trim_next_time_frame_candles
            )

        return Candles(
            candles=candles,
            time_frame=self.time_frame,
            next_time_frame_candles=next_candles
        )

    def find_next_n_distribution_candles_after_index(self, index_after_candle, n: int) -> List[Candle]:
        candles = []
        for candle in self[index_after_candle + 1:]:
            if candle.is_distribution_candle():
                candles.append(candle)
            if len(candles) == n:
                break

        return candles

    def find_next_n_accumulation_candles_after_index(self, index_after_candle, n: int) -> List[Candle]:
        candles = []
        for candle in self[index_after_candle + 1:]:
            if candle.is_distribution_candle():
                candles.append(candle)
            if len(candles) == n:
                break

        return candles

    def get_candles_between(self, start_candle_time, end_candle_time, time_frame) -> List[Candle]:
        candles_between = []
        if self.time_frame != time_frame:
            if self.next_time_frame_candles is not None:
                return self.next_time_frame_candles.get_candles_between(
                    start_candle_time=start_candle_time,
                    end_candle_time=end_candle_time,
                    time_frame=time_frame
                )
        else:
            for candle in self:
                if candle.open_time >= start_candle_time and candle.close_time <= end_candle_time:
                    candles_between.append(candle)
                elif candle.open_time >= end_candle_time:
                    return candles_between

    def __len__(self):
        return len(self.candles)

    def __getitem__(self, item):
        return self.candles[item]

    def __iter__(self):
        return iter(self.candles)

    def has_ladder_broken_for_leg(self, leg: Candle, above: bool):
        candles = self.get_candles_after(leg.close_time)
        if above:
            return len([c for c in candles if c.low > leg.low]) > 0
        else:
            return len([c for c in candles if c.high > leg.high]) > 0

    def find_greediest_distribution_candle_inside(self, leg: Candle, after: Optional[Candle]) -> Optional[Candle]:
        greediest = None
        for c in self:
            if after is not None and not c.is_after(after):
                continue

            if c.is_inside(leg) and (greediest is None or leg.low < c.open < greediest.open) and \
                    c.is_distribution_candle():
                greediest = c
        return greediest

    def find_greediest_accumulation_candle_inside(self, leg: Candle, after: Optional[Candle]) -> Optional[Candle]:
        greediest = None
        for c in self:
            if after is not None and not c.is_after(after):
                continue

            if c.is_inside(leg) and (greediest is None or leg.high > c.open > greediest.open) and \
                    c.is_accumulation_candle():
                greediest = c
        return greediest

    def apply_min_year(self, min_year: int) -> 'Candles':
        candles = [c for c in self if c.open_time.date().year > min_year]
        self.candles = candles
        return self

    def find_highest_candle_after(self, candle: 'Candle'):
        highest_candle = None
        for c in self:
            if c.is_after(candle):
                if highest_candle is None:
                    highest_candle = c
                elif c.is_above(highest_candle):
                    highest_candle = c

        if highest_candle is None:
            return self.next_time_frame_candles.find_highest_candle_after(candle)

        return highest_candle

    def find_lowest_candle_after(self, candle: 'Candle'):
        lowest_candle = None
        for c in self:
            if c.is_after(candle):
                if lowest_candle is None:
                    lowest_candle = c
                elif c.is_below(lowest_candle):
                    lowest_candle = c

        if lowest_candle is None:
            return self.next_time_frame_candles.find_lowest_candle_after(candle)

        return lowest_candle

    def find_lowest_completed_accumulation_candle_between(
            self,
            min_price: float,
            max_price: float,
            previous_is_accumulation: bool
    ) -> Candle:
        potential = []
        for i, c in enumerate(self[:-1]):
            if max_price > c.open > min_price and c.is_accumulation_candle():
                potential.append((i, c))

        lowest = None
        for i, c in potential:
            is_hard_closed = False
            for y, other in enumerate(self[i + 1:]):
                if c.is_wick_hard_closed_by(other):
                    is_hard_closed = True
            if is_hard_closed:
                continue

            if i == 0:
                previous_is_right_color = True
            else:
                previous_is_right_color = self[i - 1].is_accumulation_candle() \
                    if previous_is_accumulation else self[i - 1].is_distribution_candle()

            if lowest is not None and c.is_below(lowest) and previous_is_right_color:
                lowest = c
            if lowest is None and previous_is_right_color:
                lowest = c
        if lowest is not None:
            return lowest

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.find_lowest_completed_accumulation_candle_between(
                min_price=min_price,
                max_price=max_price,
                previous_is_accumulation=previous_is_accumulation
            )

    def find_highest_completed_accumulation_candle_between(self, min_price: float, max_price: float) -> Candle:
        highest = None
        for c in self[:-1]:
            if max_price > c.open > min_price and c.is_accumulation_candle():
                if highest is not None and c.is_above(highest):
                    highest = c
                if highest is None:
                    highest = c
        if highest is not None:
            return highest

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.find_highest_completed_accumulation_candle_between(
                min_price=min_price,
                max_price=max_price
            )

    def find_lowest_completed_distribution_candle_between(self, min_price: float, max_price: float) -> Candle:
        lowest = None
        for c in self[:-1]:
            if max_price > c.open > min_price and c.is_distribution_candle():
                if lowest is not None and c.is_below(lowest):
                    lowest = c
                if lowest is None:
                    lowest = c
        if lowest is not None:
            return lowest

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.find_lowest_completed_distribution_candle_between(
                min_price=min_price,
                max_price=max_price
            )

    def find_highest_completed_distribution_candle_between(
            self,
            min_price: float,
            max_price: float,
            previous_is_accumulation: bool
    ) -> Candle:
        potential = []
        for i, c in enumerate(self[:-1]):
            if max_price > c.open > min_price and c.is_distribution_candle():
                potential.append((i, c))

        highest = None
        for i, c in potential:
            is_hard_closed = False
            for y, other in enumerate(self[i + 1:]):
                if c.is_wick_hard_closed_by(other):
                    is_hard_closed = True
            if is_hard_closed:
                continue
            if i == 0:
                previous_is_right_color = True
            else:
                previous_is_right_color = self[i - 1].is_accumulation_candle() \
                    if previous_is_accumulation else self[i - 1].is_distribution_candle()

            if highest is not None and c.is_above(highest) and previous_is_right_color:
                highest = c
            if highest is None and previous_is_right_color:
                highest = c
        if highest is not None:
            return highest

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.find_highest_completed_distribution_candle_between(
                min_price=min_price,
                max_price=max_price,
                previous_is_accumulation=previous_is_accumulation
            )

    def find_lowest_completed_accumulation_candle_after(self, candle: 'Candle') -> Candle:
        lowest = None
        for c in self[:-1]:
            if c.is_after(candle) and c.is_accumulation_candle():
                if lowest is not None and c.is_below(lowest):
                    lowest = c
                if lowest is None:
                    lowest = c
        if lowest is not None:
            return lowest

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.find_highest_completed_accumulation_candle_after(candle=candle)

    def find_highest_completed_accumulation_candle_after(self, candle: 'Candle') -> Candle:
        highest = None
        for c in self[:-1]:
            if c.is_after(candle) and c.is_accumulation_candle():
                if highest is not None and c.is_above(highest):
                    highest = c
                if highest is None:
                    highest = c

        if highest is not None:
            return highest

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.find_highest_completed_accumulation_candle_after(candle=candle)

        raise Exception('invalid candles')

    def find_highest_completed_distribution_candle_after(self, candle: 'Candle') -> Candle:
        highest = None
        for c in self[:-1]:
            if c.is_after(candle) and c.is_distribution_candle() and c.is_completed():
                if highest is not None and c.is_above(highest):
                    highest = c
                if highest is None:
                    highest = c

        if highest is not None:
            return highest

        if self.next_time_frame_candles is not None:
            return self.next_time_frame_candles.find_highest_completed_distribution_candle_after(candle=candle)

        raise Exception('invalid candles')

    def tick(self, time_frame: TimeFrame) -> List['Candles']:
        pass

    def get_reversal_bars(self) -> List[Tuple[int, Candle]]:
        reversal_bars = []
        is_uptrend = False
        for i, c in enumerate(self):
            if i == 0:
                continue

            potential_uptrend_reversal = is_uptrend and c.is_distribution_candle()
            potential_downtrend_reversal = not is_uptrend and c.is_accumulation_candle()

            if len(reversal_bars) == 0 or potential_uptrend_reversal or potential_downtrend_reversal:
                for other_candle in reversed(self[0:i]):
                    if other_candle.is_opposite_color_candle(c):
                        if c.is_reversal_bar_for(other_candle):
                            is_uptrend = c.is_accumulation_candle()
                            reversal_bars.append((i, c))
                        break

        return reversal_bars

    def get_poly_state(
            self,
            index_candle: int,
            current_state: None
    ) -> str:


        candle = self.candles[index_candle]
        # other_candle = self.candles[index_start_for_state]
        other_candle = self.candles[index_candle - 1]

        # Need to rework as we need previous candle not the next candle

        hh_up = other_candle.high > candle.high and current_state == "up" # continuation
        hh_down = (other_candle.high > candle.close or candle.high > other_candle.high) and current_state == "down" # new trend
        ll_up = (other_candle.low < candle.close or candle.low < other_candle.low) and current_state == "up" # new trend
        ll_down = other_candle.low < candle.high and current_state == "down"

        return None




 # return self[index].is_opposite_color_candle(self[index - 1]) and \
 #               self.is_candle_followed_by_n_same_color_candles(index_candle=index, n_candles=1)


