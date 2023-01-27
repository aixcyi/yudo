from datetime import date, timedelta
from itertools import chain
from typing import NamedTuple


class Segment(NamedTuple):
    start: date
    stop: date
    unit = timedelta(days=1)

    def __iter__(self):
        sign = self.start
        times = 0
        while sign < self.stop:
            sign = self.start + self.unit * times
            times += 1
            yield sign.strftime('%Y%m%d')

    def __or__(self, other):
        assert isinstance(other, self.__class__)
        if not self.start <= other.start:
            return other.__or__(self)
        if self.stop + self.unit < other.start:  # 不相交，无并集
            return None
        if self.stop < other.stop:
            return Segment(self.start, other.stop)
        return self


class SegmentSet:
    def __init__(self, segments: list[Segment]):
        segments = sorted(segments, key=lambda s: (s[0], s[1]))
        results = []
        anchor = segments.pop(0)
        for segment in segments:
            if (union := anchor | segment) is None:
                results.append(anchor)
                anchor = segment
            elif union is anchor:
                pass
            else:
                anchor = union
        else:
            results.append(anchor)
        self._segments = results

    def __iter__(self):
        return chain.from_iterable(self._segments)
