import datetime
import math
from enum import Enum

from dateutil.relativedelta import *


class TimeFrame(Enum):
    TF_1MINUTE = '1m'
    TF_3MINUTE = '3m'
    TF_5MINUTE = '5m'
    TF_15MINUTE = '15m'
    TF_1HOUR = '1h'
    TF_4HOUR = '4h'
    TF_8HOUR = '8h' # needs to be implemented
    TF_12HOUR = '12h'
    TF_1DAY = '1d'
    TF_1WEEK = '1w'
    TF_1MONTH = '1M'
    TF_1YEAR = '12M'

    def get_n_time_frames_below(self, n: int) -> 'TimeFrame':
        time_frame = self
        for i in range(0, n):
            time_frame = time_frame.get_next()
        return time_frame

    def get_next(self) -> 'TimeFrame':
        if self == TimeFrame.TF_1MINUTE:
            return self
        if self == TimeFrame.TF_3MINUTE:
            return TimeFrame.TF_1MINUTE
        if self == TimeFrame.TF_5MINUTE:
            return TimeFrame.TF_3MINUTE
        if self == TimeFrame.TF_15MINUTE:
            return TimeFrame.TF_5MINUTE
        if self == TimeFrame.TF_1HOUR:
            return TimeFrame.TF_15MINUTE
        if self == TimeFrame.TF_4HOUR:
            return TimeFrame.TF_1HOUR
        if self == TimeFrame.TF_12HOUR:
            return TimeFrame.TF_4HOUR
        if self == TimeFrame.TF_1DAY:
            return TimeFrame.TF_12HOUR
        if self == TimeFrame.TF_1WEEK:
            return TimeFrame.TF_1DAY
        if self == TimeFrame.TF_1MONTH:
            return TimeFrame.TF_1WEEK
        if self == TimeFrame.TF_1YEAR:
            return TimeFrame.TF_1MONTH

    def get_description(self) -> str:
        if self == TimeFrame.TF_1MINUTE:
            return "1 min."
        if self == TimeFrame.TF_3MINUTE:
            return "3 min."
        if self == TimeFrame.TF_5MINUTE:
            return "5 min."
        if self == TimeFrame.TF_15MINUTE:
            return "15 min."
        if self == TimeFrame.TF_1HOUR:
            return "1h"
        if self == TimeFrame.TF_4HOUR:
            return "4h"
        if self == TimeFrame.TF_12HOUR:
            return "12h"
        if self == TimeFrame.TF_1DAY:
            return "daily"
        if self == TimeFrame.TF_1WEEK:
            return "weekly"
        if self == TimeFrame.TF_1MONTH:
            return "monthly"
        if self == TimeFrame.TF_1YEAR:
            return "yearly"

    @staticmethod
    def get_minutes(tf) -> int:
        if tf == TimeFrame.TF_1MINUTE:
            return 1
        if tf == TimeFrame.TF_3MINUTE:
            return 3
        if tf == TimeFrame.TF_5MINUTE:
            return 5
        if tf == TimeFrame.TF_15MINUTE:
            return 15
        if tf == TimeFrame.TF_1HOUR:
            return 60
        if tf == TimeFrame.TF_4HOUR:
            return 240

        if tf == TimeFrame.TF_12HOUR:
            return 720

        if tf == TimeFrame.TF_1DAY:
            return 1440

        if tf == TimeFrame.TF_1WEEK:
            return 10080

        if tf == TimeFrame.TF_1MONTH:
            return 302400

        if tf == TimeFrame.TF_1YEAR:
            return 525600

    @staticmethod
    def to_datetimedelta(tf) -> datetime.timedelta:
        now = datetime.datetime.now()
        now_after_delta = now + TimeFrame.to_relativedelta(tf)

        return now_after_delta - now

    @staticmethod
    def to_relativedelta(tf, times=None) -> relativedelta:
        if tf == TimeFrame.TF_1MINUTE:
            minutes = 1
            if times is not None:
                minutes = math.ceil(minutes * times)
            return relativedelta(minutes=minutes)

        if tf == TimeFrame.TF_3MINUTE:
            minutes = 3
            if times is not None:
                minutes = math.ceil(minutes * times)
            return relativedelta(minutes=minutes)

        if tf == TimeFrame.TF_5MINUTE:
            minutes = 5
            if times is not None:
                minutes = math.ceil(minutes * times)
            return relativedelta(minutes=minutes)

        if tf == TimeFrame.TF_15MINUTE:
            minutes = 15
            if times is not None:
                minutes = math.ceil(minutes * times)
            return relativedelta(minutes=minutes)

        if tf == TimeFrame.TF_1HOUR:
            if times is not None:
                minutes = 60
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(hours=1)

        if tf == TimeFrame.TF_4HOUR:
            if times is not None:
                minutes = 240
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(hours=4)

        if tf == TimeFrame.TF_8HOUR:
            if times is not None:
                minutes = 480
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(hours=8)

        if tf == TimeFrame.TF_12HOUR:
            if times is not None:
                minutes = 720
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(hours=12)

        if tf == TimeFrame.TF_1DAY:
            if times is not None:
                minutes = 1440
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(days=1)

        if tf == TimeFrame.TF_1WEEK:
            if times is not None:
                minutes = 10080
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(weeks=1)

        if tf == TimeFrame.TF_1MONTH:
            if times is not None:
                minutes = 302400
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(months=1)

        if tf == TimeFrame.TF_1YEAR:
            if times is not None:
                minutes = 525600
                minutes = math.ceil(minutes * times)
                return relativedelta(minutes=minutes)
            return relativedelta(years=1)

    @staticmethod
    def is_lower_time_frame_then(tf: 'TimeFrame', other_tf: 'TimeFrame'):
        ordered_time_frames = [
            TimeFrame.TF_1MINUTE,
            TimeFrame.TF_3MINUTE,
            TimeFrame.TF_5MINUTE,
            TimeFrame.TF_15MINUTE,
            TimeFrame.TF_1HOUR,
            TimeFrame.TF_4HOUR,
            TimeFrame.TF_12HOUR,
            TimeFrame.TF_1DAY,
            TimeFrame.TF_1WEEK,
            TimeFrame.TF_1MONTH,
            TimeFrame.TF_1YEAR
        ]

        return ordered_time_frames.index(tf) < ordered_time_frames.index(other_tf)

    @staticmethod
    def is_same_time_frame_then(tf: 'TimeFrame', other_tf: 'TimeFrame') -> bool:
        ordered_time_frames = [
            TimeFrame.TF_1MINUTE,
            TimeFrame.TF_3MINUTE,
            TimeFrame.TF_5MINUTE,
            TimeFrame.TF_15MINUTE,
            TimeFrame.TF_1HOUR,
            TimeFrame.TF_4HOUR,
            TimeFrame.TF_12HOUR,
            TimeFrame.TF_1DAY,
            TimeFrame.TF_1WEEK,
            TimeFrame.TF_1MONTH,
            TimeFrame.TF_1YEAR
        ]

        return ordered_time_frames.index(tf) == ordered_time_frames.index(other_tf)

    @staticmethod
    def is_lower_time_frame_or_equal_then(tf: 'TimeFrame', other_tf: 'TimeFrame') -> bool:
        ordered_time_frames = [
            TimeFrame.TF_1MINUTE,
            TimeFrame.TF_3MINUTE,
            TimeFrame.TF_5MINUTE,
            TimeFrame.TF_15MINUTE,
            TimeFrame.TF_1HOUR,
            TimeFrame.TF_4HOUR,
            TimeFrame.TF_12HOUR,
            TimeFrame.TF_1DAY,
            TimeFrame.TF_1WEEK,
            TimeFrame.TF_1MONTH,
            TimeFrame.TF_1YEAR
        ]

        return ordered_time_frames.index(tf) <= ordered_time_frames.index(other_tf)

    @staticmethod
    def is_higher_time_frame_or_equal_then(tf: 'TimeFrame', other_tf: 'TimeFrame') -> bool:
        ordered_time_frames = [
            TimeFrame.TF_1MINUTE,
            TimeFrame.TF_3MINUTE,
            TimeFrame.TF_5MINUTE,
            TimeFrame.TF_15MINUTE,
            TimeFrame.TF_1HOUR,
            TimeFrame.TF_4HOUR,
            TimeFrame.TF_12HOUR,
            TimeFrame.TF_1DAY,
            TimeFrame.TF_1WEEK,
            TimeFrame.TF_1MONTH,
            TimeFrame.TF_1YEAR
        ]

        return ordered_time_frames.index(tf) >= ordered_time_frames.index(other_tf)

    @staticmethod
    def is_higher_time_frame_then(tf: 'TimeFrame', other_tf: 'TimeFrame') -> bool:
        ordered_time_frames = [
            TimeFrame.TF_1MINUTE,
            TimeFrame.TF_3MINUTE,
            TimeFrame.TF_5MINUTE,
            TimeFrame.TF_15MINUTE,
            TimeFrame.TF_1HOUR,
            TimeFrame.TF_4HOUR,
            TimeFrame.TF_12HOUR,
            TimeFrame.TF_1DAY,
            TimeFrame.TF_1WEEK,
            TimeFrame.TF_1MONTH,
            TimeFrame.TF_1YEAR
        ]

        return ordered_time_frames.index(tf) > ordered_time_frames.index(other_tf)


ALL_TIME_FRAMES = [
    TimeFrame.TF_1MINUTE,
    TimeFrame.TF_3MINUTE,
    TimeFrame.TF_5MINUTE,
    TimeFrame.TF_15MINUTE,
    TimeFrame.TF_1HOUR,
    TimeFrame.TF_4HOUR,
    TimeFrame.TF_12HOUR,
    TimeFrame.TF_1DAY,
    TimeFrame.TF_1WEEK,
    TimeFrame.TF_1MONTH,
    TimeFrame.TF_1YEAR
]
