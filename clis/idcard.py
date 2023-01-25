import sys
from itertools import product
from typing import Any

import click
from click import Parameter, Context, ParamType

from core.idcard import enum_adcode, enum_seq, enum_birth_by_ymd, patch_checksum, enum_birth_by_age
from core.meaningfuls import fmt_datasize


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


@click.command(help='穷举所有可能的身份证号码。')
@click.option('-p', '--province', multiple=True, help='省级代码，可输入多个。')
@click.option('-c', '--city', multiple=True, help='市级代码，可输入多个。')
@click.option('-t', '--county', multiple=True, help='县级代码，可输入多个。')
@click.option('-y', '--year', multiple=True, type=int, help='出生年份。可以输入多个。')
@click.option('-m', '--month', multiple=True, type=int, help='出生月份。可以输入多个。')
@click.option('-d', '--day', multiple=True, type=int, help='出生日期（指公历月份的哪一天）。可以输入多个。')
@click.option('-a', '--age', type=Age(), help='年龄（18）、范围（[0,18]）、集合（{12,18,20}）。')
@click.option('-M', '--male', is_flag=True, help='男性。')
@click.option('-F', '--female', is_flag=True, help='女性。男女同时选择等效于同时不选择。')
@click.option('-s', '--checksum', multiple=True, help='校验码。身份证最后一位。可输入多个。')
@click.option('-f', '--force', is_flag=True, help='不提示数量，直接输出。')
def enumidc(
        province, city, county,
        year, month, day, age,
        male, female, checksum, force,
):
    seqs = tuple(enum_seq(male, female))
    codes = tuple(enum_adcode(province, city, county))
    births = tuple(enum_birth_by_age(age) if age else enum_birth_by_ymd(year, month, day))
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

    qty = len(seqs) * len(codes) * len(births) * (len(checksum) if checksum else 1)
    dsz = fmt_datasize(qty * 20)
    tip = f'预估数据量 {qty:d} 条，文本 {dsz}，确定继续？(Y/n)'
    if force is False:
        print(tip, end=' ', file=sys.stderr)
        if input()[:1] != 'Y':
            return

    ids = map(patch_checksum, product(codes, births, seqs))
    ids = filter(lambda i: i[-1] in checksum, ids) if checksum else ids
    print('\n'.join(ids))
