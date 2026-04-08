import traceback
from typing import List, Tuple, Optional

from domain.candles.candle import Candle
from domain.candles.candles import Candles
from domain.trends.trend import Trend


class TrendFactory:
    def get_uptrends(self, candles: Candles, exterior_trend: Trend = None) -> List[Trend]:
        sorted_candles: List[Tuple[int, Candle]] = self.sort_ascending_distribution_candles(
            candles=candles,
            exterior_trend=exterior_trend
        )
        valid_trends: List[Trend] = self.get_trends(
            candles=candles,
            sorted_candles=sorted_candles,
            exterior_trend=exterior_trend
        )

        if candles.next_time_frame_candles is not None:
            massaged_trends = self.massage_trends(candles.next_time_frame_candles, valid_trends)
            valid_trends.extend(massaged_trends)

            next_time_frame_trends = self.get_uptrends(
                candles=candles.next_time_frame_candles,
                exterior_trend=valid_trends[-1] if len(valid_trends) > 0 else exterior_trend
            )
            valid_trends.extend(next_time_frame_trends)

        return valid_trends

    def get_downtrends(self, candles: Candles, exterior_trend: Trend = None) -> List[Trend]:
        sorted_candles = self.sort_descending_accumulation_candles(candles=candles, exterior_trend=exterior_trend)
        valid_trends: List[Trend] = self.get_trends(
            candles=candles,
            sorted_candles=sorted_candles,
            exterior_trend=exterior_trend
        )

        if candles.next_time_frame_candles is not None:
            massaged_trends = self.massage_trends(candles=candles, previous_time_frame_trends=valid_trends)
            valid_trends.extend(massaged_trends)

            next_time_frame_trends = self.get_downtrends(
                candles=candles.next_time_frame_candles,
                exterior_trend=valid_trends[-1] if len(valid_trends) > 0 else exterior_trend
            )
            valid_trends.extend(next_time_frame_trends)

        return valid_trends

    def get_trends(
            self,
            candles: Candles,
            sorted_candles: List[Tuple[int, Candle]],
            exterior_trend: Trend = None,
            array_trends: bool = True
    ):
        valid_trends: List[Trend] = []
        if len(sorted_candles) == 0:
            return []

        max_reach_point_index = max([c[0] for c in sorted_candles]) - 1
        i = 0
        base_point = sorted_candles[0]
        if exterior_trend is not None and array_trends:
            base_point = self.find_next_arrayed_trend_base_point(
                candles=candles,
                exterior_trend=exterior_trend
            )

        while base_point is not None:
            trend = self.get_trend_from_base_point(
                candles=candles,
                base_point=base_point,
                exterior_trend=exterior_trend if array_trends else None,
                max_reach_point_index=max_reach_point_index
            )

            if trend is None:
                break

            if trend.is_valid():
                valid_trends.append(trend)

            if array_trends:
                if exterior_trend is None or trend.is_inside(exterior_trend):
                    exterior_trend = trend
                    base_point = self.find_next_arrayed_trend_base_point(candles=candles, exterior_trend=trend)
                else:
                    base_point = None
            else:
                if i < len(sorted_candles) -1:
                    i += 1
                    base_point = sorted_candles[i]
                else:
                    base_point = None

        return valid_trends

    def sort_ascending_distribution_candles(
            self,
            candles: Candles,
            exterior_trend: Trend = None
    ) -> List[Tuple[int, Candle]]:
        distribution_candle_index_tuple: List[Tuple[int, Candle]] = candles.get_all_distribution_candles_index_tuple()
        if exterior_trend is not None:
            reach_point_candle = exterior_trend.get_reach_point_candle()
            distribution_candle_index_tuple = list(filter(
                lambda c: reach_point_candle.is_before(c[1]),
                distribution_candle_index_tuple
            ))

        distribution_candle_index_tuple.sort(key=lambda candle: candle[1].low)

        return candles.filter_candles_by_index(distribution_candle_index_tuple)

    def massage_trends(self, candles: Candles, previous_time_frame_trends: List[Trend]) -> List[Trend]:
        massaged_trends = []
        sorted_distribution_candles: List[Tuple[int, Candle]] = self.sort_ascending_distribution_candles(candles)
        sorted_accumulation_candles: List[Tuple[int, Candle]] = self.sort_descending_accumulation_candles(candles)
        if len(sorted_accumulation_candles) == 0:
            print('empty sorted accumulation candles {}'.format(candles.time_frame))
            return []
        if len(sorted_distribution_candles) == 0:
            print('empty sorted distribution candles {}'.format(candles.time_frame))
            return []

        max_accumulation_reach_point_index = max([c[0] for c in sorted_accumulation_candles])
        max_distribution_reach_point_index = max([c[0] for c in sorted_distribution_candles])

        for trend in previous_time_frame_trends:
            base_point_candle = trend.get_base_point_candle()
            reach_point_candle = trend.get_reach_point_candle()
            base_point = self.get_trend_point_for_candle(candles=candles, candle=base_point_candle)
            reach_point = self.get_trend_point_for_candle(candles=candles, candle=reach_point_candle)
            if base_point is None:
                continue
            if reach_point is None:
                continue

            is_uptrend = base_point_candle.is_distribution_candle()
            refined_base_point = self.refine_trend_point_candle(
                candles=candles,
                candle=base_point_candle,
                is_uptrend=is_uptrend
            )
            refined_reach_point = self.refine_trend_point_candle(
                candles=candles,
                candle=reach_point_candle,
                is_uptrend=is_uptrend
            )
            massaged_trend = Trend(
                base_point=base_point,
                reach_point=reach_point,
                is_massaged=trend.is_massaged,
                n_massaged=trend.n_massaged,
                refined_base_point_candle=refined_base_point,
                refined_reach_point_candle=refined_reach_point
            )

            if massaged_trend.is_uptrend():
                max_reach_point_index = max_distribution_reach_point_index
            else:
                max_reach_point_index = max_accumulation_reach_point_index

            self.adapt_trend(
                candles=candles,
                trend=massaged_trend,
                max_reach_point_index=max_reach_point_index,
                is_massaging=True
            )

            if massaged_trend.is_valid() and massaged_trend.is_massaged_from(trend):
                massaged_trends.append(massaged_trend)

        if candles.next_time_frame_candles is not None:
            next_time_frame_massaged_trends = self.massage_trends(
                candles=candles.next_time_frame_candles,
                previous_time_frame_trends=massaged_trends
            )
            massaged_trends.extend(next_time_frame_massaged_trends)

        return massaged_trends

    def adapt_trend(
            self,
            trend: Trend,
            candles: Candles,
            max_reach_point_index: int,
            is_massaging: bool = False
    ) -> 'Trend':
        start = trend.get_reach_point_index() + 1
        end = max_reach_point_index + 1

        for x in range(start, end):
            candle_x = candles[x]
            y = trend.calculate_trend_value_for_candle(candle=candle_x)

            if candle_x.hard_closes_level(y) and candle_x.is_completed() and \
                    candle_x.is_same_color_candle(trend.get_base_point_candle()):
                trend.set_soft_hard_close_candle(candle_x)

            if candle_x.is_opposite_color_candle(trend.get_base_point_candle()):
                continue
            if candle_x.breaks_trend_from_base_point(trend.get_base_point_candle()):
                trend.set_trend_break_candle(candle_x)
                break

            if candle_x.hard_closes_level(y) and candle_x.is_completed():
                self.set_reach_point(
                    trend=trend,
                    i=x,
                    candle=candle_x,
                    candles=candles
                )
                if is_massaging:
                    trend.is_massaged = True
                    trend.n_massaged += 1

                trend.set_soft_hard_close_candle(None)
                self.adapt_trend(
                    trend=trend,
                    max_reach_point_index=max_reach_point_index,
                    is_massaging=is_massaging,
                    candles=candles
                )
                break

        n_touches = 0
        for candle in candles[trend.get_base_point_index():]:
            if trend.is_touched_by(candle):
                trend.add_touch(candle)
        trend.n_touches = n_touches

        return trend

    def set_reach_point(
            self,
            trend: Trend,
            i: int,
            candle: Candle,
            candles: Candles
    ):
        refined_reach_point_candle = self.refine_trend_point_candle(
            candles=candles,
            candle=candle,
            is_uptrend=trend.is_uptrend()
        )
        trend.set_reach_point(i=i, candle=candle, refined_reach_point_candle=refined_reach_point_candle)

    def get_trend_point_for_candle(self, candles: Candles, candle: Candle) -> Optional[Tuple[int, Candle]]:
        for i, c in enumerate(candles):
            if c.close_time == candle.close_time:
                return i, candle
        return None

    def refine_trend_point_candle(self, candles: Candles, candle: Candle, is_uptrend: bool) -> Candle:
        for c in candles:
            if c.open_time > candle.close_time:
                break

            if c.open_time > candle.open_time and \
                    c.close_time <= candle.close_time:
                if is_uptrend:
                    is_at_trend_reach_point = c.low == candle.low
                else:
                    is_at_trend_reach_point = c.high == candle.high

                if is_at_trend_reach_point:
                    if candles.next_time_frame_candles is not None:
                        return self.refine_trend_point_candle(
                            candles=candles.next_time_frame_candles,
                            candle=c,
                            is_uptrend=is_uptrend
                        )
                    return c

        return candle

    def get_trend_from_base_point(
            self,
            base_point: Tuple[int, Candle],
            candles: Candles,
            exterior_trend: Optional[Trend],
            max_reach_point_index: int
    ) -> Optional[Trend]:
        reach_point = self.find_next_reach_point(
            base_point_index=base_point[0],
            exterior_trend=exterior_trend,
            candles=candles
        )
        if reach_point is None:
            return None

        is_uptrend = base_point[1].is_distribution_candle()

        refined_base_point = self.refine_trend_point_candle(
            candle=base_point[1],
            candles=candles,
            is_uptrend=is_uptrend
        )

        refined_reach_point = self.refine_trend_point_candle(
            candles=candles,
            candle=reach_point[1],
            is_uptrend=is_uptrend
        )

        trend = Trend(
            base_point=base_point,
            reach_point=reach_point,
            exterior_trend=exterior_trend,
            refined_base_point_candle=refined_base_point,
            refined_reach_point_candle=refined_reach_point
        )

        try:
            self.adapt_trend(
                candles=candles,
                trend=trend,
                max_reach_point_index=max_reach_point_index
            )
        except Exception as err:
            print(err)
            print(traceback.format_exc())
            return None

        return trend

    def find_reach_point(self, sorted_candles, base_point) -> Optional[Tuple[int, Candle]]:
        for c in sorted_candles:
            if c[0] > base_point[0]:
                return c
        return None

    def find_next_reach_point(
            self,
            candles: Candles,
            base_point_index: int,
            exterior_trend: Optional[Trend] = None
    ) -> Optional[Tuple[int, Candle]]:
        base_point_candle = candles[base_point_index]

        min_datetime = None
        if exterior_trend is not None:
            min_datetime = exterior_trend.get_reach_point_time()

        for i, c in enumerate(candles[base_point_index + 1:]):
            if min_datetime is not None and c.open_time <  min_datetime:
                continue

            if c.is_same_color_candle(base_point_candle):
                return i + base_point_index + 1, c

        return None

    def find_next_arrayed_trend_base_point(
            self,
            candles: Candles,
            exterior_trend: Trend
    ) -> Optional[Tuple[int, Candle]]:
        max_distance = None
        next_base_point = None
        if exterior_trend is None:
            return None
        trend_reach_point_index = exterior_trend.get_reach_point_index()

        for i, c in enumerate(candles):
            if i <= trend_reach_point_index:
                continue
            if c.is_opposite_color_candle(exterior_trend.get_reach_point_candle()):
                continue
            distance = exterior_trend.get_distance_from(c)
            if max_distance is None or distance > max_distance:
                max_distance = distance
                next_base_point = i, c

        if max_distance is not None and max_distance >= 0:
            return next_base_point

        return None

    def sort_descending_accumulation_candles(
            self,
            candles: Candles,
            exterior_trend: Trend = None
    ) -> List[Tuple[int, Candle]]:
        accumulation_candle_index_tuples: List[Tuple[int, Candle]] = candles.get_all_accumulation_candles_index_tuple()
        if exterior_trend is not None:
            reach_point_candle = exterior_trend.get_reach_point_candle()
            accumulation_candle_index_tuples = list(filter(
                lambda c: reach_point_candle.is_before(c[1]),
                accumulation_candle_index_tuples
            ))

        accumulation_candle_index_tuples.sort(key=lambda candle: candle[1].high, reverse=True)

        return candles.filter_candles_by_index(accumulation_candle_index_tuples)