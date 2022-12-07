"""
生成指定类型的随机数据。
"""
import sys
from argparse import ArgumentParser

from mocks.binary import BinaryMock, BinaryType, parse_bits
from mocks.dt import DatetimeMock, str2delta, DatetimeType
from mocks.ipaddress import IPv4AddressMock, IPv6AddressMock
from mocks.uuids import UUIDType, UUIDMock


def construct():
    app = ArgumentParser(prog='mock', description=__doc__)
    sub = app.add_subparsers(dest='operation', title='operations')

    # ================================
    binary = sub.add_parser('bin', help='二进制数据。')
    binary.epilog = '算法名称：\n  ' + ', '.join(sorted(BinaryMock.ALGORITHMS.keys()))
    binary.add_argument('length', metavar='<LENGTH>', help='比特数，后缀以B表字节数；也可以是常见杂凑算法名称。')
    types = binary.add_mutually_exclusive_group(required=True)
    types.add_argument('-b', '--base', choices=[64, 85, 32], type=int, help='输出 base64／base85／base32')
    types.add_argument('-x', '--hex', action='store_true', help='输出 HEX。')
    types.add_argument('-X', '--hex-array', action='store_true', help='输出十六进制字节数组。')
    types.add_argument('-D', '--dec-array', action='store_true', help='输出十进制字节数组。')
    style = binary.add_argument_group(title='styles', description='仅在 -X|-D 中可用。')
    style.add_argument('--sep', help='每个字节的间隔符。默认为 "," 。')
    style.add_argument('--prefix', help='每个字节的前缀。默认为空。')
    style.add_argument('--suffix', help='每个字节的后缀。默认为空。')
    style.add_argument('--head', help='每串字节集的头部，一般是 "{"，此处默认为空。')
    style.add_argument('--tail', help='每串字节集的尾部，一般是 "}"，此处默认为空。')

    # ================================
    dt = sub.add_parser('time', help='日期时间与时间戳。')
    dt.epilog = 'Format: https://docs.python.org/zh-cn/3/library/datetime.html#strftime-and-strptime-format-codes'
    dt.add_argument('delta', help='时间差，用于确定随机范围。正数辅以后缀：秒s／分钟m／小时h／天d／星期w')
    dt.set_defaults(types=DatetimeType.DATETIME)
    mode = dt.add_mutually_exclusive_group(required=True)
    mode.add_argument('-a', '--after', action='store_const', const='after', dest='mode',
                      help='基于现在的随机范围 [now, now+delta]')
    mode.add_argument('-b', '--before', action='store_const', const='before', dest='mode',
                      help='基于现在的随机范围 [now-delta, now]')
    mode.add_argument('-c', '--cross', action='store_const', const='cross', dest='mode',
                      help='基于现在的随机范围 [now-delta, now+delta]')
    scope = dt.add_mutually_exclusive_group(required=False)
    scope.add_argument('-f', '--format', default='%Y-%m-%d %H:%M:%S',
                       help='以指定格式输出日期时间。默认为 "%%Y-%%m-%%d %%H:%%M:%%S" 。')
    scope.add_argument('-m', '--millisecond', action='store_const', dest='types', const=DatetimeType.TS_MS_INT,
                       help='以毫秒为单位的整数时间戳。')
    scope.add_argument('-s', '--second', action='store_const', dest='types', const=DatetimeType.TS_SEC_INT,
                       help='以秒为单位的整数时间戳。')
    scope.add_argument('-S', '--sec-float', action='store_const', dest='types', const=DatetimeType.TS_SEC_FLOAT,
                       help='以秒为单位的浮点数时间戳。')

    # ================================
    uuid = sub.add_parser('uuid', help='全局唯一ID。')
    uuid.description = '默认以全球唯一编号（GUID）格式输出。'
    uuid.set_defaults(types=UUIDType.UUID)
    types = uuid.add_mutually_exclusive_group()
    types.add_argument('-x', '--hex', action='store_const', dest='types', const=UUIDType.HEX, help='以 HEX 格式输出。')
    types.add_argument('-i', '--int', action='store_const', dest='types', const=UUIDType.INT, help='以整数形式输出。')
    types.add_argument('-u', '--urn', action='store_const', dest='types', const=UUIDType.URN, help='以 URN 形式输出。')

    # ================================
    ipv4 = sub.add_parser('ipv4', help='IPv4协议地址。')
    space = ipv4.add_mutually_exclusive_group()
    space.add_argument('-n', '--network', help='生成范围为某个网络。格式："网络号/掩码"。')
    space.add_argument('-r', '--range', nargs=2, help='生成范围为两个地址之间，包括两个端点。')

    # ================================
    ipv6 = sub.add_parser('ipv6', help='IPv6协议地址。')
    ipv6.add_argument('-c', '--compatible', action='store_true', help='生成IPv4映射地址。')

    # ================================
    id_usage = (
        '\n  mock id [-h | --help]'
        '\n  mock id [-q <QTY>] [-o] [-m|-f] [--min <AGE_MIN>] [--max <AGE_MAX>]'
        '\n  mock id [-q <QTY>] --mask <REGEX>'
    )
    idcard = sub.add_parser('id', help='身份证号。', usage=id_usage)
    idcard.add_argument('-o', '--old', action='store_true', help='输出旧版15位号码而不是新版18位。')
    idcard.add_argument('-m', '--male', action='store_true', help='仅限男性。')
    idcard.add_argument('-f', '--female', action='store_true', help='仅限女性。')
    idcard.add_argument('--min', default=20, type=int, help='年龄的最小值，正整数。默认为20。')
    idcard.add_argument('--max', default=40, type=int, help='年龄的最大值，正整数。默认为40。')
    idcard.add_argument('--mask', help='掩码。')

    # ================================
    for _sub in (v for k, v in locals().items()
                 if k != 'app' and v.__class__ is ArgumentParser):
        _sub.add_argument('-q', '--qty', default='10', type=int, help='要输出的数量，默认 10 个。')
    return app


class OperatingException(Exception):

    def __init__(self, msg: str):
        self.message = msg


class Operator:
    class OperatingError(Exception):
        message: str = ''

        def __init__(self, msg: str):
            self.message = msg

    def __init__(self):
        parser = construct()
        namespace = parser.parse_args(sys.argv[2:])
        if (op := namespace.operation) is None or not hasattr(self, op):
            parser.parse_args(sys.argv[1:] + ['-h'])
            sys.exit(0)
        func = getattr(self, op)
        if namespace.qty > 99999:
            print('数据量过大，是否继续？（Y/n）', end='', file=sys.stderr)
            if input() != 'Y':
                sys.exit(0)
        try:
            func(namespace, cycle=range(namespace.qty))
        except self.OperatingError as e:
            print(e.message)

    @staticmethod
    def bin(namespace, cycle):
        # 每一行的比特数目
        bits = parse_bits(namespace.length, Operator.OperatingError)
        if bits < 1:
            raise Operator.OperatingError('binary长度无意义。')

        # 二进制转字符的编码类型
        if namespace.base:
            coding = BinaryType(BinaryType.BASE | namespace.base)
        elif namespace.hex_array:
            coding = BinaryType.ARRAY_HEX
        elif namespace.dec_array:
            coding = BinaryType.ARRAY_DEC
        else:
            coding = BinaryType.HEX

        # 生成数据
        worker = BinaryMock(bits, coding)
        worker.seperator = namespace.sep if namespace.sep else worker.seperator
        worker.prefix = namespace.prefix if namespace.prefix else worker.prefix
        worker.suffix = namespace.suffix if namespace.suffix else worker.suffix
        worker.head = namespace.head if namespace.head else worker.head
        worker.tail = namespace.tail if namespace.tail else worker.tail
        worker.mock(cycle).pprint()

    @staticmethod
    def time(namespace, cycle):
        worker = DatetimeMock.near_mode(
            types=namespace.types,
            mode=namespace.mode,
            delta=str2delta(namespace.delta),
        )
        worker.fmt = namespace.format if namespace.format else worker.fmt
        worker.mock(cycle).pprint()

    @staticmethod
    def uuid(namespace, cycle):
        worker = UUIDMock(namespace.types)
        worker.mock(cycle).pprint()

    @staticmethod
    def ipv4(namespace, cycle):
        if namespace.network:
            try:
                worker = IPv4AddressMock.network_mode(namespace.network)
            except (ValueError, TypeError, OverflowError) as e:
                raise OperatingException(msg=str(e))
        else:

            worker = IPv4AddressMock(start, stop)
        worker.mock(cycle).pprint()

    @staticmethod
    def ipv6(namespace, cycle):
        worker = IPv6AddressMock()
        worker.mock(cycle, namespace.compatible)
        worker.pprint()

    # @staticmethod
    # def id(namespace, cycle):
    #     t = (namespace.male, namespace.female)
    #     gender = 'Male' if t == (True, False) else 'Female' if t == (False, True) else 'Both'
    #     bits = 15 if namespace.old else 18
    #     age_min = namespace.min if namespace.min else 0
    #     age_max = namespace.max if namespace.max else 70
    #     provinces = namespace.province if namespace.province else PROVINCES
    #     cities = ()
    #     counties = ()
    #
    #     results = (make_id() for _ in cycle)
    #     print('\n'.join(results))


Operator()
