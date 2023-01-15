"""
         __
        /\ \    Power script for aixcyi
       //\\ \   and all contributors
      // /\\ \  run on Python 3.10
     // /  \\ \   __
    // /____\\ \// /
   // _______\\// /  生成指定类型的随机数据。
  // /        ><-<
 // /        //\\ \
//_/        //_/\\_\
"""

__all__ = [
    'paser',
    'maps',
]

from argparse import ArgumentParser

from mock.binary import ALGORITHMS
from mock.dt import DatetimeType
from mock.uuids import UUIDType

app = ArgumentParser(prog='mock', description=__doc__)
sub = app.add_subparsers(dest='operation', title='operations')

# ================================
binary = sub.add_parser('bin', help='二进制数据。')
binary.epilog = '算法名称：\n  ' + ', '.join(sorted(ALGORITHMS.keys()))
binary.add_argument('length', metavar='<LENGTH>', help='比特数，后缀以B表字节数；也可以是常见杂凑算法名称。')
types = binary.add_mutually_exclusive_group(required=True)
types.add_argument('-x', '--hex', action='store_true', help='输出纯HEX。')
types.add_argument('-b', '--base', choices=[64, 85, 32], type=int, help='输出 base64／base85／base32')
types.add_argument('-X', '--hex-array', action='store_true', help='输出十六进制字节数组。')
types.add_argument('-D', '--dec-array', action='store_true', help='输出十进制字节数组。')
style = binary.add_argument_group(title='styles', description='仅在 -X|-D 中可用。')
style.add_argument('--bpg', help='一组多少个字节，负数表示倒着数。默认为 1 。')
style.add_argument('--sep', help='每组之间的间隔符。默认为 "," 。')
style.add_argument('--prefix', help='每组的前缀。默认为空。')
style.add_argument('--suffix', help='每组的后缀。默认为空。')
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
subpasers = tuple(v for k, v in locals().items() if k != 'app' and v.__class__ is ArgumentParser)
for _sub in subpasers:
    _sub.add_argument('-q', '--qty', default='10', type=int, help='要输出的数量，默认 10 个。')

# ================================
# public interface
paser = app
maps = {
    'bin': 'binary',
}
