__all__ = [
    'str2delta',
    'DatetimeType',
    'DatetimeMock',
]

import re
from datetime import datetime, timedelta
from enum import IntEnum
from random import randint
from typing import Literal

from mocks.basic import Mock


def str2delta(string: str) -> timedelta:
    result = re.match(r'([0-9]*\.?[0-9]+)([smhdw])', string)
    if result is None:
        return timedelta(days=1)
    value, unit = result.groups()
    unit = {'s': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks',
            }[unit]
    return timedelta(**{unit: int(value)})


class DatetimeType(IntEnum):
    TS_SEC_INT = 1
    """秒级整数时间戳。"""
    TS_SEC_FLOAT = 2
    """秒级小数时间戳。"""
    TS_MS_INT = 3
    """毫秒级整数时间戳。"""
    DATETIME = 5
    """自定义格式的日期时间。"""


class DatetimeMock(Mock):

    @classmethod
    def near_mode(cls,
                  types: DatetimeType,
                  mode: Literal['before', 'after', 'cross'],
                  delta: timedelta):
        now = datetime.now()
        match mode:
            case 'before':
                start = now - delta
                stop = now
            case 'after':
                start = now
                stop = now + delta
            case 'cross':
                start = now - delta
                stop = now + delta
            case _:
                raise ValueError
        return cls(types, start, stop)

    def __init__(self, types: DatetimeType, start: datetime, stop: datetime):
        self._type = types
        self.fmt = '%Y-%m-%d %H:%M:%S'
        match types:
            # 毫秒级精度
            case DatetimeType.TS_SEC_FLOAT | DatetimeType.TS_MS_INT:
                self._min = int(start.timestamp() * 1000)
                self._max = int(stop.timestamp() * 1000)
            # 秒级精度
            case DatetimeType.TS_SEC_INT | DatetimeType.DATETIME:
                self._min = int(start.timestamp())
                self._max = int(stop.timestamp())
            case _:
                raise ValueError

    def mock(self, cycle, *args, **kwargs):
        ds = (randint(self._min, self._max) for _ in cycle)
        match self._type:
            case DatetimeType.TS_SEC_INT | DatetimeType.TS_MS_INT:
                pass
            case DatetimeType.TS_SEC_FLOAT:
                ds = map(lambda s: s / 1000, ds)
            case DatetimeType.DATETIME:
                ds = map(lambda s: s / 1000, ds)
                ds = map(datetime.fromtimestamp, ds)
            case _:
                raise ValueError
        self._dataset = ds
        return self

    def output(self, *args, **kwargs):
        return map(str, self._dataset)
