import re
from datetime import datetime, date, timedelta

import click as cli

from core.meaningfuls import fmt_datasize
from core.structs import Segment, SegmentSet

ZODIACS = '鼠牛虎兔龙蛇马羊猴鸡狗猪'
DATE_FORMAT = '%Y.%m.%d'


class RawRange(cli.ParamType):
    name = 'raw_range'

    def __init__(self, inner_type: type):
        self._type = inner_type
        assert self._type in (int, date, timedelta)

    def convert(self, value: str, param, ctx) -> tuple:
        try:
            a, _, p = value.partition(',')
            a, _, b = a.partition('~')
            if not b and not p:
                a = b = value
            return self._bound(a), self._bound(b), self._plus(p)
        except ValueError as e:
            msg = e.args[0]
            self.fail(msg, param, ctx)
        except TypeError:
            raise

    def _bound(self, value: str):
        """
        解析用户输入的区间边界。

        :param value: 被解析的字符串。
        :return: types 类型的值。
        :raise TypeError: types 不支持。
        :raise ValueError: 解析失败。
        """
        if self._type is int:
            return int(value)
        if self._type is date:
            return datetime.strptime(value, DATE_FORMAT).date()
        if self._type is timedelta:
            negative = value.startswith('-')
            value = value[1:] if negative else value
            deltas = re.findall(r'(\d+)([ymdsw])', value)
            if not (_v := ''.join(''.join(d) for d in deltas)) == value:
                raise ValueError(f'{value} 解析得到 {_v}')
            summary = sum(
                int(qty) *
                {'y': 365, 'm': 30, 'd': 1, 's': 90, 'w': 7}[unit]
                for qty, unit in deltas
            )
            return timedelta(days=-summary if negative else summary)
        raise TypeError()

    def _plus(self, value: str):
        """
        解析附带元素。
        """
        if self._type is int:
            return int(value) if value else date.today().year
        if self._type is date:
            return None
        if self._type is timedelta:
            return datetime.strptime(value, DATE_FORMAT).date() if value else date.today()
        raise TypeError()


@cli.command()
@cli.option('-f', '--format', 'fmt', default=DATE_FORMAT,
            help=f'输出格式，默认为“{DATE_FORMAT}”。日期作为参数时格式固定为“yyyy.mm.dd”。')
@cli.option('-i', '--interval', 'days', metavar='MIN[~MAX]', type=RawRange(date), multiple=True,
            help='每个 -i 直接输出一个日期，或范围内的所有日期。')
@cli.option('-a', '--age', 'ages', metavar='MIN[~MAX][,YEAR]', type=RawRange(int), multiple=True,
            help='每个 -a 输出范围内的所有日期，范围的最大最小值由 YEAR 年时的年龄确定。')
@cli.option('-o', '--offset', 'offsets', metavar='LEFT[~RIGHT][,BASE]', type=RawRange(timedelta), multiple=True,
            help='每个 -o 输出范围内的所有日期，范围的左右两边由基于 BASE 的偏移量决定。\n'
                 'BASE 默认是当天。偏移量正则表达为“-?(\\d+[ymdsw]){1,}”，\n'
                 '其中后缀“d”表示一天，1m(月)=30d，1y(年)=365d，1w(星期)=7d，1s(季度)=3m=90d。')
@cli.option('-z', '--zodiacs', help='过滤不在这些生肖年的日期，例如“虎兔龙蛇”。生肖年按公历算。')
@cli.option('-r', '--regex', help='过滤不能完全匹配正则表达式的(格式化后的)日期。')
@cli.option('-F', '--force', is_flag=True, help='不提示数量，直接穷举输出所有日期。')
def gend(
        fmt: str,
        days: tuple[tuple[date, date, None]],
        ages: tuple[tuple[int, int, int]],
        offsets: tuple[tuple[timedelta, timedelta, date]],
        regex: str,
        zodiacs: str,
        force: bool,
):
    """生成指定格式的日期（不含时间）。"""
    try:
        date(1949, 10, 1).strftime(fmt)
    except ValueError:
        cli.secho('输出格式有误。', err=True, fg='yellow')
        return
    try:
        pattern = re.compile(regex) if regex else None
    except re.error:
        cli.secho('正则表达式有误。', err=True, fg='yellow')
        return
    offsets = [Segment(root + a, root + b) for a, b, root in offsets] if offsets else []
    days = [Segment(min(a, b), max(a, b)) for a, b, _ in days] if days else []
    ages = [
        # 因为是减法，所以是要base减去a、b中比较大的那个，
        # 才能得到比较小的具体日期，进而令 Segment 的 start <= stop
        Segment(
            date(year - max(a, b), 1, 1),
            date(year - min(a, b), 12, 31),
        )
        for a, b, year in ages
    ] if ages else []

    dates = iter(SegmentSet(offsets + days + ages))
    dates = filter(lambda d: ZODIACS[(d.year - 4) % 12] in zodiacs, dates) if zodiacs else dates
    dates = map(lambda d: d.strftime(fmt), dates)
    dates = filter(lambda d: re.fullmatch(pattern, d), dates) if pattern else dates
    dates = tuple(dates)
    qty = len(dates)
    dsz = fmt_datasize(len(dates[0]) * qty if dates else 0)
    tip = f'预估数据量 {qty:d} 条，文本 {dsz}，确定继续？(Y/[n]) '
    if qty == 0:
        cli.secho('没有产生任何数据。', err=True, fg='yellow')
        return
    if force is False:
        cli.echo(tip, err=True, nl=False)
        if input()[:1] != 'Y':
            return
    print('\n'.join(dates))
