from datetime import date, timedelta
from itertools import chain
from typing import NamedTuple, Any, NoReturn


class Segment(NamedTuple):
    start: date
    stop: date
    unit: Any = timedelta(days=1)

    def __iter__(self):
        sign = self.start
        times = 0
        while sign < self.stop:
            sign = self.start + self.unit * times
            times += 1
            yield sign

    def __or__(self, other):
        assert isinstance(other, self.__class__)
        if not self.start <= other.start:
            return other.__or__(self)
        if self.stop + self.unit < other.start:  # 不相交，无并集
            return None
        if self.stop < other.stop:
            return Segment(self.start, other.stop)
        return self

    def __neg__(self):
        if self.stop >= self.start:
            return self
        return Segment(self.stop, self.start, self.unit)


class SegmentSet:
    _segments: list[Segment] = []

    def __init__(self, segments: list[Segment]):
        self._merge(segments)

    def __iter__(self):
        return chain.from_iterable(self._segments)

    def __or__(self, other):
        if isinstance(other, list):
            self._merge(other)
        elif isinstance(other, SegmentSet):
            self._merge(other._segments)
        else:
            raise TypeError()
        return self

    def _merge(self, segments: list[Segment]) -> NoReturn:
        segments += self._segments
        segments = sorted(segments, key=lambda s: (s[0], s[1]))
        results = []
        if not segments:
            return

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
