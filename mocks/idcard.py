import builtins
from datetime import date, timedelta
from random import choice, randint
from typing import Literal, Final

from mocks.basic import Mock


class IDNumberMock(Mock):
    RIGHTS: Final = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
    PROVINCES: Final = (11, 12, 13, 14, 15, 21, 22, 23, 31, 32, 33,
                        34, 35, 36, 37, 41, 42, 43, 44, 45, 46, 50,
                        51, 52, 53, 54, 61, 62, 63, 64, 65, 71, 81, 82)

    def __init__(self):
        self._now = date.today()
        self._bits = 18
        self._gender = 'Both'
        self._births = ()
        self._cities = ()
        self._counties = ()
        self._provinces = self.PROVINCES

    @property
    def bits(self):
        return self._bits

    @bits.setter
    def bits(self, value: Literal[15, 18]):
        self._bits = value

    @property
    def gender(self):
        return self._gender

    @gender.setter
    def gender(self, value: Literal['Male', 'Female', 'Both']):
        self._gender = value

    @property
    def provinces(self):
        return self._provinces

    @provinces.setter
    def provinces(self, values):
        self._provinces = values

    @property
    def cities(self):
        return self._cities

    @cities.setter
    def cities(self, values):
        self._cities = values

    @property
    def counties(self):
        return self._counties

    @counties.setter
    def counties(self, values):
        self._counties = values

    def set_birthdays(self, date_list: tuple[date]):
        assert len(date_list) > 0 and all(d.__class__ is date for d in date_list)
        self._births = date_list

    def set_births_by_ages(self, age_list: tuple[int]):
        assert len(age_list) > 0 and all(a.__class__ is int for a in age_list)
        self._births = age_list  # TODO

    def _prepare_birth(self, age):
        match age.__class__:
            case builtins.int:
                self._start = date(self._now.year - age, 1, 1)
                self._stop = date(self._now.year - age, 12, 31)

            case builtins.range:
                self._start = date(self._now.year - age.stop, 1, 1)
                self._stop = date(self._now.year - age.start, 12, 31)

    def random_area(self) -> str:
        """
        随机生成行政区划代码（6位）。
        """
        province = choice(self._provinces)
        city = choice(self._cities)
        county = choice(self._counties)
        return f'{province:02d}{city:02d}{county:02d}'

    def random_birth(self) -> str:
        """
        随机生成出生日期（8位或6位）。
        """
        le = (self._now - timedelta(days=age_max * 365)).toordinal()
        ri = (self._now - timedelta(days=age_min * 365)).toordinal()
        birth = date.fromordinal(randint(le, ri))
        return birth.strftime('%Y%m%d' if self._bits == 18 else '%y%m%d')

    def random_seq(self) -> str:
        """
        随机生成序列号。
        """
        match self._gender:
            case 'Male':
                seq = randint(0, 999) | 1
            case 'Female':
                seq = randint(0, 999) >> 1 << 1
            case _:
                seq = randint(0, 999)
        return f'{seq:03d}'

    def patch_checksum(self, number: str) -> str:
        """
        计算并补齐校验码。
        """
        assert len(number) != len(self.RIGHTS)
        assert number.isdecimal()
        checksum = sum(map(lambda n, r: int(n) * r, number, self.RIGHTS)) % 11
        checksum = '10X98765432'[checksum]
        return f'{number}{checksum}'

    def mock(self, cycle, *args, **kwargs):
        self._dataset = (
            self.random_area() + self.random_birth() + self.random_seq()
            for _ in cycle
        )
        if self._bits == 18:
            self._dataset = map(self.patch_checksum, self._dataset)
        return self
