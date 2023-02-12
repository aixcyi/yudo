import re
from datetime import datetime, date, timedelta, timezone
from types import UnionType
from typing import Pattern

import click

from core.click_chore import Regex, ask
from core.structs import Segment, SegmentSet
from core.style import *

ZODIACS = '鼠牛虎兔龙蛇马羊猴鸡狗猪'
DATE_FORMAT = '%Y.%m.%d'
DATETIME_FORMAT = f'{DATE_FORMAT}+%H:%M:%S'


class RawRange(click.ParamType):
    name = 'raw_range'

    def __init__(self, inner_type: type | UnionType):
        self._type = inner_type

    def convert(self, value: str, param, ctx) -> tuple:
        try:  # 命令行表达：a[~b][,p]
            a, _, p = value.partition(',')
            a, _, b = a.partition('~')
            if not b and not p:
                a = b = value
            elif not b:
                b = a
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
        if self._type is int:  # 直接指定年龄
            return int(value)
        if self._type is datetime:  # 直接指定时间（允许只有日期）
            try:
                return datetime.strptime(value, DATETIME_FORMAT)
            except ValueError:
                return datetime.strptime(value, DATE_FORMAT)
        if self._type is date:  # 直接指定日期
            return datetime.strptime(value, DATE_FORMAT).date()
        if self._type == timedelta | date:  # 基于BASE这一天的偏移量
            negative = value.startswith('-')
            value = value[1:] if negative else value
            deltas = re.findall(r'(\d+)([ymdsw])', value)
            if not (_v := ''.join(''.join(d) for d in deltas)) == value:
                raise ValueError(f'{value} 解析得到 {_v}')
            summary = sum(
                int(qty) * {'y': 365, 'm': 30, 'd': 1, 's': 90, 'w': 7}[unit]
                for qty, unit in deltas
            )
            return timedelta(days=-summary if negative else summary)
        if self._type is float:  # 直接指定秒戳/毫秒戳
            return float(value)
        if self._type == timedelta | datetime:  # 基于BASE这一刻的偏移量
            negative = value.startswith('-')
            value = value[1:] if negative else value
            deltas = re.findall(r'(\d+)([hmsf])', value)
            if not (_v := ''.join(''.join(d) for d in deltas)) == value:
                raise ValueError(f'{value} 解析得到 {_v}')
            summary = sum(
                int(qty) * {'h': 3600 * 1000, 'm': 60 * 1000, 's': 1 * 1000, 'f': 1}[unit]
                for qty, unit in deltas
            )
            delta = timedelta(days=summary // 1000, milliseconds=summary % 1000)
            return -delta if negative else delta
        raise TypeError()

    def _plus(self, value: str):
        """
        解析附带元素。
        """
        if self._type is int:  # 年龄区间的尾缀是BASE，用以表明年龄是基于哪一年的
            return int(value) if value else date.today().year
        if self._type is date:  # 直接指定日期区间的话不会有尾缀
            return None
        if self._type is timedelta:  # 偏移量区间有个BASE，用以表明偏移量是基于哪一天
            return datetime.strptime(value, DATE_FORMAT).date() if value else date.today()
        if self._type is float:  # 时间戳区间尾缀一个时区
            return datetime.strptime(value, '%z').tzinfo
        if self._type is datetime:  # 直接指定时间区间的话不会有尾缀
            return None
        raise TypeError()


@click.command('enumd', short_help='穷举范围内的日期')
@click.option('-f', '--format', 'fmt', default=DATE_FORMAT,
              help=f'输出格式，默认为“{DATE_FORMAT}”。日期作为参数时格式固定为“yyyy.mm.dd”。')
@click.option('-i', '--interval', 'days',
              metavar='MIN[~MAX]', type=RawRange(date), multiple=True,
              help='每个 -i 直接输出一个日期，或范围内的所有日期。')
@click.option('-a', '--age', 'ages',
              metavar='MIN[~MAX][,YEAR]', type=RawRange(int), multiple=True,
              help='每个 -a 输出范围内的所有日期，范围的最大最小值由 YEAR 年时的年龄确定。')
@click.option('-o', '--offset', 'offsets',
              metavar='LEFT[~RIGHT][,BASE]', type=RawRange(timedelta | date), multiple=True,
              help='每个 -o 输出范围内的所有日期，范围的左右两边由基于 BASE 的偏移量决定。\n'
                   'BASE 默认是当天。偏移量正则表达为“-?(\\d+[ymdsw]){1,}”，\n'
                   '其中后缀“d”表示一天，1m(月)=30d，1y(年)=365d，1w(星期)=7d，1s(季度)=3m=90d。')
@click.option('-z', '--zodiacs', help='过滤不在这些生肖年的日期，例如“虎兔龙蛇”。生肖年按公历算。')
@click.option('-r', '--regex', type=Regex(), help='过滤不能完全匹配正则表达式的(格式化后的)日期。')
@click.option('-F', '--force', is_flag=True, help='不提示数量，直接穷举输出所有日期。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def enum_date(
        fmt: str,
        days: tuple[tuple[date, date, None]],
        ages: tuple[tuple[int, int, int]],
        offsets: tuple[tuple[timedelta, timedelta, date]],
        regex: Pattern,
        zodiacs: str,
        force: bool,
):
    """
    穷举范围内的日期（不含时间），并以自定义格式输出。递增量为1天。
    """
    try:
        date(1949, 10, 1).strftime(fmt)
    except ValueError:
        click.secho('输出格式有误。', err=True, fg=PT_WARNING)
        return

    offsets = [-Segment(root + a, root + b) for a, b, root in offsets] if offsets else []
    days = [-Segment(a, b) for a, b, _ in days] if days else []
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
    dates = filter(lambda d: re.fullmatch(regex, d), dates) if regex else dates
    dates = tuple(dates)
    if ask(dates, force):
        print('\n'.join(dates))


@click.command('enumdt', short_help='穷举范围内的日期时间')
@click.option('-f', '--format', 'fmt', default=DATETIME_FORMAT,
              help=f'输出格式，默认为{DATETIME_FORMAT}。\n时间作为参数时格式固定为yyyy.mm.dd[+HH:MM:SS]。')
@click.option('-i', '--interval', 'intervals',
              metavar='MIN[~MAX]', type=RawRange(datetime), multiple=True,
              help='每个 -i 直接输出一个时间，或范围内的所有时间。')
@click.option('-t', '--timestamp', 'stamps',
              metavar='MIN[~MAX][,ZONE]', type=RawRange(float), multiple=True,
              help='每个 -t 输出范围内的所有时间，范围的最大最小值由 ZONE 时区的秒级时间戳确定。\n'
                   '时间戳可以是小数。ZONE 的格式为±HHMM[SS[.ffffff]]。')
@click.option('-o', '--offset', 'offsets',
              metavar='MIN[~MAX][,BASE]', type=RawRange(timedelta | datetime), multiple=True,
              help='每个 -o 输出范围内的所有时间，范围的左右两边由基于 BASE 的偏移量决定。\n'
                   'BASE 默认是此时此刻。偏移量正则表达为“-?(\\d+[hmsf]){1,}”，\n'
                   '其中后缀“s”表示一秒，1m(分钟)=60s，1h(小时)=60m=3600s，1f(毫秒)=0.001s。')
@click.option('-r', '--regex', type=Regex(), help='过滤不能完全匹配正则表达式的(格式化后的)日期。')
@click.option('-m', '--millisecond', 'is_ms_base', help='以毫秒为单位（默认是秒）进行穷举。')
@click.option('-F', '--force', is_flag=True, help='不提示数量，直接穷举输出所有时间。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def enum_datetime(
        fmt: str,
        intervals: tuple[tuple[datetime, datetime, None]],
        stamps: tuple[tuple[float, float, timezone]],
        offsets: tuple[tuple[timedelta, timedelta, datetime]],
        regex: Pattern,
        is_ms_base: bool,
        force: bool,
):
    """
    穷举范围内的日期时间，并以自定义格式输出。递增量默认为1秒。
    """
    try:
        datetime(1949, 10, 1, 12, 0, 0).strftime(fmt)
    except ValueError:
        click.secho('输出格式有误。', err=True, fg=PT_WARNING)
        return

    def _p(t: float, tz: timezone) -> datetime:
        return datetime.fromtimestamp(t, tz)

    unit = timedelta(microseconds=1) if is_ms_base else timedelta(seconds=1)
    stamps = [-Segment(_p(a, tz), _p(b, tz), unit) for a, b, tz in stamps] if stamps else []
    offsets = [-Segment(root + a, root + b, unit) for a, b, root in offsets] if offsets else []
    intervals = [-Segment(a, b) for a, b, _ in intervals] if intervals else []

    moments = iter(SegmentSet(offsets + intervals + stamps))
    moments = map(lambda d: d.strftime(fmt), moments)
    moments = filter(lambda d: re.fullmatch(regex, d), moments) if regex else moments
    moments = tuple(moments)
    if ask(moments, force):
        print('\n'.join(moments))
