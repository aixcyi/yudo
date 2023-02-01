import json
import sys
from typing import Any, Sequence, Iterable
from datetime import date
from itertools import product
from math import ceil

from click import Parameter, Context, ParamType, command, option

from core.meaningfuls import fmt_datasize
from core.structs import SegmentSet, Segment

RIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)

with open(r'./code2022.json', 'r', encoding='UTF-8') as f:
    ad_codes = tuple(k[:6] for k in json.load(f).keys() if k.endswith('000000'))


def mk_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).strftime('%Y%m%d')
    except ValueError:
        return None


def enum_adcode(
        provinces: Sequence = None,
        cities: Sequence = None,
        counties: Sequence = None,
) -> Iterable:
    codes = (c for c in ad_codes if not c.endswith('0000'))
    codes = (c for c in codes if c[0:2] in provinces) if provinces else codes
    codes = (c for c in codes if c[2:4] in cities) if cities else codes
    codes = (c for c in codes if c[4:6] in counties) if counties else codes
    return codes


def enum_birth_by_ymd(
        year: Iterable = None,
        month: Iterable = None,
        day: Iterable = None,
) -> Iterable:
    day = day if day else range(1, 31 + 1)
    year = year if year else range(1900, 2100 + 1)
    month = month if month else range(1, 12 + 1)
    dates = (mk_date(y, m, d) for y, m, d in product(year, month, day))
    dates = filter(None, dates)
    return dates


def enum_birth_by_age(ages: Iterable, base: date = date.today()):
    ms = SegmentSet([
        Segment(
            base.replace(base.year - age, 1, 1),
            base.replace(base.year - age, 12, 31),
        )
        for age in ages
    ])
    return iter(ms)


def enum_seq(male: bool = False, female: bool = False) -> Iterable:
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


class Age(ParamType):
    name = 'age'

    def convert(self, value: Any, param: Parameter | None, ctx: Context | None) -> Any:
        value = str(value).strip()
        try:
            if value.startswith('{'):
                ages = tuple(set(map(int, value[1:-1].split(','))))
                assert len(ages) > 0
            elif value.startswith('['):
                ages = tuple(map(int, value[1:-1].split(',')))
                assert len(ages) == 2
                ages = tuple(range(ages[0], ages[1] + 1))
            else:
                ages = (int(value),)
                assert ages[0] > 0
            return ages

        except (ValueError, AssertionError):
            msg = '年龄这个参数的格式有误。'
            self.fail(msg, param, ctx)


class Checksum(ParamType):
    name = 'checksum'

    def convert(self, value: Any, param: Parameter | None, ctx: Context | None) -> Any:
        if len(value) == 1:
            if value in '0123456789X':
                return value
        msg = '提供的身份证号码最后一位（checksum）是错误的。'
        self.fail(msg, param, ctx)


@command('genidc', deprecated=True)
@option('-p', '--province', multiple=True, help='省级代码，可输入多个。')
@option('-c', '--city', multiple=True, help='市级代码，可输入多个。')
@option('-t', '--county', multiple=True, help='县级代码，可输入多个。')
@option('-y', '--year', multiple=True, type=int, help='出生年份。可以输入多个。')
@option('-m', '--month', multiple=True, type=int, help='出生月份。可以输入多个。')
@option('-d', '--day', multiple=True, type=int, help='出生日期（指公历月份的哪一天）。可以输入多个。')
@option('-a', '--age', type=Age(), help='年龄（18）、范围（[0,18]）、集合（{12,18,20}）。')
@option('-M', '--male', is_flag=True, help='男性。')
@option('-F', '--female', is_flag=True, help='女性。男女同时选择等效于同时不选择。')
@option('-s', '--checksum', multiple=True, help='校验码。身份证最后一位。可输入多个。')
@option('-f', '--force', is_flag=True, help='不提示数量，直接输出。')
def generate_prcid(
        province, city, county,
        year, month, day, age,
        male, female, checksum, force,
):
    """穷举所有可能的身份证号码。"""
    seqs = tuple(enum_seq(male, female))
    codes = tuple(enum_adcode(province, city, county))
    births = tuple(enum_birth_by_age(age) if age else enum_birth_by_ymd(year, month, day))
    checksum = ''.join(checksum)
    if not seqs:
        print('没有匹配的序列号。', file=sys.stderr)
        return
    if not codes:
        print('没有匹配的行政区划代码。', file=sys.stderr)
        return
    if not births:
        print('没有匹配的出生日期。', file=sys.stderr)
        return
    if checksum and not all(c in '0123456789X' for c in checksum):
        print('每个校验码只能为 0、1、2、3、4、5、6、7、8、9、X 之一。', file=sys.stderr)
        return

    qty = len(seqs) * len(codes) * len(births)
    qty = ceil(qty / 11 * len(checksum)) if checksum else qty
    dsz = fmt_datasize(qty * 20)
    tip = f'预估数据量 {qty:d} 条，文本 {dsz}，确定继续？(Y/n)'
    if force is False:
        print(tip, end=' ', file=sys.stderr)
        if input()[:1] != 'Y':
            return

    ids = map(patch_checksum, product(codes, births, seqs))
    ids = filter(lambda i: i[-1] in checksum, ids) if checksum else ids
    print('\n'.join(ids))
