import json
import typing
from datetime import date, timedelta
from itertools import product, chain

RIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)

with open(r'./code2022.json', 'r', encoding='UTF-8') as f:
    ad_codes = tuple(k[:6] for k in json.load(f).keys() if k.endswith('000000'))


class Segment(typing.NamedTuple):
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


class MorseSegment:
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
        print(self._segments)
        c = chain.from_iterable(self._segments)
        return c


def mk_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).strftime('%Y%m%d')
    except ValueError:
        return None


def pase_birth(pattern: str):
    """解析类正则表达式。"""
    # \d、[]、[^]


def enum_adcode(
        provinces: typing.Sequence = None,
        cities: typing.Sequence = None,
        counties: typing.Sequence = None,
) -> typing.Iterable:
    codes = (c for c in ad_codes if not c.endswith('0000'))
    codes = (c for c in codes if c[0:2] in provinces) if provinces else codes
    codes = (c for c in codes if c[2:4] in cities) if cities else codes
    codes = (c for c in codes if c[4:6] in counties) if counties else codes
    return codes


def enum_birth_by_ymd(
        year: typing.Iterable = None,
        month: typing.Iterable = None,
        day: typing.Iterable = None,
) -> typing.Iterable:
    day = day if day else range(1, 31 + 1)
    year = year if year else range(1900, 2100 + 1)
    month = month if month else range(1, 12 + 1)
    dates = (mk_date(y, m, d) for y, m, d in product(year, month, day))
    dates = filter(None, dates)
    return dates


def enum_birth_by_age(ages: typing.Iterable, base: date = date.today()):
    ms = MorseSegment([
        Segment(
            base.replace(base.year - age, 1, 1),
            base.replace(base.year - age, 12, 31),
        )
        for age in ages
    ])
    return iter(ms)


def enum_seq(male: bool = False, female: bool = False) -> typing.Iterable:
    match male, female:
        case True, False:
            seqs = range(1, 995 + 1, 2)
        case False, True:
            seqs = range(2, 995 + 1, 2)
        case _:
            seqs = range(1, 995 + 1)  # 996~999 是百岁老人专用号码

    return map(lambda i: f'{i:03d}', seqs)


def patch_checksum(*digits) -> str:
    number = ''.join(digits[0])
    if len(number) < 17:
        raise ValueError()

    return number[:17] + {
        0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7',
        6: '6', 7: '5', 8: '4', 9: '3', 10: '2',
    }[sum(map(lambda d, r: int(d) * r, number, RIGHTS)) % 11]
