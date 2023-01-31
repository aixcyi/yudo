from datetime import datetime, date, timedelta, timezone
from re import findall, fullmatch, compile as compile_re, error as re_error
from types import UnionType

from click import ParamType, command, option, secho, echo

from core.meaningfuls import fmt_datasize
from core.structs import Segment, SegmentSet

ZODIACS = '鼠牛虎兔龙蛇马羊猴鸡狗猪'
DATE_FORMAT = '%Y.%m.%d'
DATETIME_FORMAT = f'{DATE_FORMAT}+%H:%M:%S'


def ask(dateset, force: bool) -> bool:
    qty = len(dateset)
    dsz = fmt_datasize(len(dateset[0]) * qty if dateset else 0)
    tip = f'预估数据量 {qty:d} 条，文本 {dsz}，确定继续？(Y/[n]) '
    if qty == 0:
        secho('没有产生任何数据。', err=True, fg='yellow')
        return False
    if force is False:
        echo(tip, err=True, nl=False)
        if input()[:1] != 'Y':
            return False
    return True


class RawRange(ParamType):
    name = 'raw_range'

    def __init__(self, inner_type: type | UnionType):
        self._type = inner_type

    def convert(self, value: str, param, ctx) -> tuple:
        try:
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
            deltas = findall(r'(\d+)([ymdsw])', value)
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
            deltas = findall(r'(\d+)([hmsf])', value)
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


@command('gend')
@option('-f', '--format', 'fmt', default=DATE_FORMAT,
        help=f'输出格式，默认为“{DATE_FORMAT}”。日期作为参数时格式固定为“yyyy.mm.dd”。')
@option('-i', '--interval', 'days', metavar='MIN[~MAX]', type=RawRange(date), multiple=True,
        help='每个 -i 直接输出一个日期，或范围内的所有日期。')
@option('-a', '--age', 'ages', metavar='MIN[~MAX][,YEAR]', type=RawRange(int), multiple=True,
        help='每个 -a 输出范围内的所有日期，范围的最大最小值由 YEAR 年时的年龄确定。')
@option('-o', '--offset', 'offsets', metavar='LEFT[~RIGHT][,BASE]', type=RawRange(timedelta | date), multiple=True,
        help='每个 -o 输出范围内的所有日期，范围的左右两边由基于 BASE 的偏移量决定。\n'
             'BASE 默认是当天。偏移量正则表达为“-?(\\d+[ymdsw]){1,}”，\n'
             '其中后缀“d”表示一天，1m(月)=30d，1y(年)=365d，1w(星期)=7d，1s(季度)=3m=90d。')
@option('-z', '--zodiacs', help='过滤不在这些生肖年的日期，例如“虎兔龙蛇”。生肖年按公历算。')
@option('-r', '--regex', help='过滤不能完全匹配正则表达式的(格式化后的)日期。')
@option('-F', '--force', is_flag=True, help='不提示数量，直接穷举输出所有日期。')
def generate_date(
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
        secho('输出格式有误。', err=True, fg='yellow')
        return
    try:
        pattern = compile_re(regex) if regex else None
    except re_error:
        secho('正则表达式有误。', err=True, fg='yellow')
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
    dates = filter(lambda d: fullmatch(pattern, d), dates) if pattern else dates
    dates = tuple(dates)
    if ask(dates, force):
        print('\n'.join(dates))


@command('gendt')
@option('-f', '--format', 'fmt', default=DATETIME_FORMAT,
        help=f'输出格式，默认为{DATETIME_FORMAT}。\n时间作为参数时格式固定为yyyy.mm.dd[+HH:MM:SS]。')
@option('-i', '--interval', 'intervals', metavar='MIN[~MAX]', type=RawRange(datetime), multiple=True,
        help='每个 -i 直接输出一个时间，或范围内的所有时间。')
@option('-t', '--timestamp', 'stamps', metavar='MIN[~MAX][,ZONE]', type=RawRange(float), multiple=True,
        help='每个 -t 输出范围内的所有时间，范围的最大最小值由 ZONE 时区的秒级时间戳确定。\n'
             '时间戳可以是小数。ZONE 的格式为±HHMM[SS[.ffffff]]。')
@option('-o', '--offset', 'offsets', metavar='MIN[~MAX][,BASE]', type=RawRange(timedelta | datetime), multiple=True,
        help='每个 -o 输出范围内的所有时间，范围的左右两边由基于 BASE 的偏移量决定。\n'
             'BASE 默认是此时此刻。偏移量正则表达为“-?(\\d+[hmsf]){1,}”，\n'
             '其中后缀“s”表示一秒，1m(分钟)=60s，1h(小时)=60m=3600s，1f(毫秒)=0.001s。')
@option('-r', '--regex', help='过滤不能完全匹配正则表达式的(格式化后的)日期。')
@option('-m', '--millisecond', 'is_ms_base', help='以毫秒为单位（默认是秒）进行穷举。')
@option('-F', '--force', is_flag=True, help='不提示数量，直接穷举输出所有时间。')
def generate_datetime(
        fmt: str,
        intervals: tuple[tuple[datetime, datetime, None]],
        stamps: tuple[tuple[float, float, timezone]],
        offsets: tuple[tuple[timedelta, timedelta, datetime]],
        regex: str,
        is_ms_base: bool,
        force: bool,
):
    """生成指定格式的日期时间。"""

    def _p(t: float, tz: timezone) -> datetime:
        return datetime.fromtimestamp(t, tz)

    try:
        datetime(1949, 10, 1, 12, 0, 0).strftime(fmt)
    except ValueError:
        secho('输出格式有误。', err=True, fg='yellow')
        return
    try:
        pattern = compile_re(regex) if regex else None
    except re_error:
        secho('正则表达式有误。', err=True, fg='yellow')
        return
    unit = timedelta(microseconds=1) if is_ms_base else timedelta(seconds=1)
    stamps = [-Segment(_p(a, tz), _p(b, tz), unit) for a, b, tz in stamps] if stamps else []
    offsets = [-Segment(root + a, root + b, unit) for a, b, root in offsets] if offsets else []
    intervals = [-Segment(a, b) for a, b, _ in intervals] if intervals else []

    moments = iter(SegmentSet(offsets + intervals + stamps))
    moments = map(lambda d: d.strftime(fmt), moments)
    moments = filter(lambda d: fullmatch(pattern, d), moments) if pattern else moments
    moments = tuple(moments)
    if ask(moments, force):
        print('\n'.join(moments))
