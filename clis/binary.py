from base64 import b64encode, b85encode, b32encode
from math import ceil
from random import getrandbits, choices
from typing import Any, Final

import click
from click.shell_completion import CompletionItem

from core.click_chore import YuConfiguration

# print(''.join(map(chr, range(32, 127))))
CHARSETS = {
    'digit': '0123456789',
    'upper': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'lower': 'abcdefghijklmnopqrstuvwxyz',
    'digit_safe': '23456789',
    'upper_safe': 'ABCDEFGHJKLMNPQRSTUVWXYZ',
    'lower_safe': 'abcdefghijklmnpqrstuvwxyz',
    'symbol': r'''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~''',
    'symbol_noshift': r"`-=[]\;',./",
    'symbol_shift': r'~!@#$%^&*()_+{}|:"<>?',
    'base16': '0123456789ABCDEF',
    'base64': '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/',
}
assert sorted(CHARSETS['symbol']) == sorted(CHARSETS['symbol_noshift'] + CHARSETS['symbol_shift'])

with YuConfiguration() as configs:
    configs.save_finally = True
    configs.ensure('charset').update(CHARSETS)


class Bytes(object):
    def __init__(
            self,
            seperator: str = '',
            prefix: str = '',
            suffix: str = '',
            head: str = '',
            tail: str = '',
    ):
        self.seperator = seperator
        self.prefix = prefix
        self.suffix = suffix
        self.head = head
        self.tail = tail

    def encode(self, data: bytes | bytearray) -> str:
        raise NotImplementedError()


class HexBytes(Bytes):
    def __init__(
            self,
            seperator: str = '',
            prefix: str = '',
            suffix: str = '',
            head: str = '',
            tail: str = '',
            bytes_per_sep: int = 1,
    ):
        super().__init__(seperator, prefix, suffix, head, tail)
        self.bytes_per_sep = bytes_per_sep
        if bytes_per_sep == 0:
            raise ValueError(
                'See parameter "bytes_per_sep" of bytes.hex() in package builtins.'
                '间隔符前后的字节数，正数从前往后数，负数从后往前数，唯独不能为0。'
            )

    def encode(self, data):
        # pure hex
        if len(self.seperator) < 1:
            return self.head + data.hex() + self.tail

        # raw bytes
        if not self.prefix and not self.suffix:
            result = data.hex(self.seperator, self.bytes_per_sep)
            return self.head + result + self.tail

        # decorated bytes
        def cut():
            step = self.bytes_per_sep
            for i in range(0, len(data), step):
                section = data[i:i + step].hex()
                yield self.prefix + section + self.suffix

        return self.head + self.seperator.join(cut()) + self.tail


class DecBytes(Bytes):
    def __init__(
            self,
            seperator: str = ',',
            prefix: str = '',
            suffix: str = '',
            head: str = '',
            tail: str = '',
    ):
        super().__init__(seperator, prefix, suffix, head, tail)
        if not seperator:
            raise ValueError(
                'Cannot ignore seperator when you translate to decimal format.'
                '将binary转换为基于非十六进制的字符串时，间隔符不能不填。'
            )

    def encode(self, data):
        mid = (f'{self.prefix}{byte:d}{self.suffix}' for byte in data)
        return self.head + self.seperator.join(mid) + self.tail


class BaseBytes(object):
    BASE_LIST: Final = (64, 85, 32)

    def __init__(self, base: int):
        if base not in self.BASE_LIST:
            raise ValueError(
                'argument must be one of base64, base85 and base32.'
                '你只能在 Base64、Base85、Base32 之中选一个。'
            )
        self._base = base

    def encode(self, data) -> str:
        match self._base:
            case 64:
                mid = b64encode(data)
            case 85:
                mid = b85encode(data)
            case 32:
                mid = b32encode(data)
            case _:
                raise ValueError()
        return str(mid, encoding='ASCII')

    # 真的需要直接替换对象方法以达到更快的速度吗？

    # def encode64(self, data) -> str:
    #     return str(b64encode(data), encoding='ASCII')
    #
    # def encode85(self, data) -> str:
    #     return str(b85encode(data), encoding='ASCII')
    #
    # def encode32(self, data) -> str:
    #     return str(b32encode(data), encoding='ASCII')


class PythonicBytes(HexBytes):
    # b"\xd7\xd3\xd2\xed"

    def __init__(self):
        super().__init__(prefix=r'\x', head=r'b"', tail='"')


class BitLength(click.ParamType):
    ALGORITHMS: Final = {
        'SM3': 256, 'MD2': 128, 'MD4': 128, 'MD5': 128,
        'SHA-224': 224, 'SHA3-224': 224, 'SHA-512/224': 224,
        'SHA-256': 256, 'SHA3-256': 256, 'SHA-512/256': 256,
        'SHA-384': 384, 'SHA3-384': 384, 'SHA-0': 160,
        'SHA-512': 512, 'SHA3-512': 512, 'SHA-1': 160,
    }

    name = 'bit_length'

    def convert(self, value: Any, param, ctx) -> Any:
        if value in self.ALGORITHMS:
            return self.ALGORITHMS[value]
        try:
            return int(value)
        except ValueError:
            msg = (
                    '比特数必须是一个正整数，或者是以下算法所代表的杂凑值比特数：\n'
                    + '、'.join(self.ALGORITHMS.keys())
            )
            self.fail(msg, param, ctx)

    def shell_complete(self, ctx, param, incomplete: str) -> list[CompletionItem]:
        algorithms = self.ALGORITHMS.keys()
        algorithms = filter(lambda a: a.startswith(incomplete), algorithms) if incomplete else algorithms
        algorithms = tuple(algorithms)
        assert algorithms
        return [CompletionItem(a) for a in algorithms]


@click.command('randbit', short_help='随机生成一定数量比特的字节串（bytes）')
@click.argument('bits', type=BitLength())
@click.option('-q', '--qty', type=int, default=1, help='生成多少串字节串（每行一串）。')
@click.option('-x', '--hex', 'hexadecimal', is_flag=True, help='以十六进制数组（HEX）格式输出。')
@click.option('-d', '--dec', 'decimal', is_flag=True, help='以十进制数组格式输出。默认输出HEX。')
@click.option('-i', '--int', 'integer', is_flag=True, help='以单个整数形式输出。默认输出HEX。')
@click.option('--b64', '--base64', is_flag=True, help='base64编码后输出。默认输出HEX。')
@click.option('--b85', '--base85', is_flag=True, help='base85编码后输出。默认输出HEX。')
@click.option('--b32', '--base32', is_flag=True, help='base32编码后输出。默认输出HEX。')
@click.option('--group', default=1, type=int, help='多少字节一组（默认1）。')
@click.option('--seperator', default='', help='每组之间的间隔符。')
@click.option('--prefix', default='', help='每组字节的前缀。')
@click.option('--suffix', default='', help='每组字节的后缀。')
@click.option('--head', default='', help='开头的前缀。')
@click.option('--tail', default='', help='结尾的尾缀。')
@click.help_option('-h', '--help')
def generate_bits(
        bits, qty, hexadecimal, decimal, integer, b64, b85, b32,
        group, seperator, prefix, suffix, head, tail
):
    """
    随机生成 BITS 比特的字节串，并以某种格式输出为文本。
    """
    if integer:
        op = None
    elif b64 or b85 or b32:
        op = BaseBytes(64 if b64 else 85 if b85 else 32)
    elif decimal:
        op = DecBytes(seperator, prefix, suffix, head, tail)
    else:
        op = HexBytes(seperator, prefix, suffix, head, tail, group)

    qb = ceil(bits / 8)  # quantity of bytes
    ds = (getrandbits(bits) for _ in range(qty))
    ds = (op.encode(d.to_bytes(qb, 'little')) for d in ds) if op else (str(d) for d in ds)
    print('\n'.join(ds))


@click.command('randstr', short_help='随机生成一定长度的字符串')
@click.argument('length', type=int)
@click.option('-d', '--digit', is_flag=True, help='向自定义字符集中添加阿拉伯数字。')
@click.option('-D', '--digit-safe', is_flag=True, help='向自定义字符集中添加阿拉伯数字，除了数字0和1。')
@click.option('-l', '--lowercase', '-a', is_flag=True, help='向自定义字符集中添加小写字母。')
@click.option('-L', '--lowercase-safe', is_flag=True, help='向自定义字符集中添加小写字母，除了小写字母l。')
@click.option('-u', '--uppercase', '-A', is_flag=True, help='向自定义字符集中添加大写字母。')
@click.option('-U', '--uppercase-safe', is_flag=True, help='向自定义字符集中添加大写字母，除了大写字母I和O。')
@click.option('-s', '--symbol', is_flag=True, help='向自定义字符集中添加键盘上的所有可见符号。')
@click.option('-c', '--symbol-normal', is_flag=True, help='向自定义字符集中添加键盘上所有无需shift的可见符号。')
@click.option('-C', '--symbol-shift', is_flag=True, help='向自定义字符集中添加键盘上所有需要shift的可见符号。')
@click.option('--b16', '--base16', '-x', is_flag=True, help='使用base16编码字符集。')
@click.option('--b64', '--base64', is_flag=True, help='使用base64编码字符集，不包含=号。')
@click.option('-m', '--line-max', type=int, help='每行最多放几个字符。')
@click.help_option('-h', '--help')
def generate_chars(
        length: int,
        digit: bool, digit_safe: bool,
        lowercase: bool, lowercase_safe: bool,
        uppercase: bool, uppercase_safe: bool,
        symbol: bool, symbol_normal: bool, symbol_shift: bool,
        b16: bool, b64: bool,
        line_max: int,
):
    """
    随机生成 LENGTH 个字符。

    通常来说，如果要生成按比特数计的字符串，更建议用 randbit 命令。
    """
    charset_cus = ''.join([
        '' if not digit else CHARSETS['digit'],
        '' if not uppercase else CHARSETS['upper'],
        '' if not lowercase else CHARSETS['lower'],
        '' if not digit_safe else CHARSETS['digit_safe'],
        '' if not uppercase_safe else CHARSETS['upper_safe'],
        '' if not lowercase_safe else CHARSETS['lower_safe'],
        '' if not symbol else CHARSETS['symbols'],
        '' if not symbol_normal else CHARSETS['synbols_noshift'],
        '' if not symbol_shift else CHARSETS['synbols_shift'],
    ])
    if b16:
        charset = CHARSETS['base16']
    elif b64:
        charset = CHARSETS['base64']
    elif charset_cus:
        charset = charset_cus
    else:
        click.secho('未设置字符集。', err=True, fg='yellow')
        return

    result = ''.join(choices(charset, k=length))
    if line_max > 0:
        for i in range(0, len(result), line_max):
            print(result[i:i + line_max])
    else:
        print(result)
