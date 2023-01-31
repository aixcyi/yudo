from math import ceil
from random import getrandbits
from typing import Final, Any

from click import command, argument, option, ParamType, Parameter, Context
from click.shell_completion import CompletionItem

from core.binary import HexBytes, DecBytes


class BitLength(ParamType):
    ALGORITHMS: Final = {
        'SM3': 256, 'MD2': 128, 'MD4': 128, 'MD5': 128,
        'SHA-224': 224, 'SHA3-224': 224, 'SHA-512/224': 224,
        'SHA-256': 256, 'SHA3-256': 256, 'SHA-512/256': 256,
        'SHA-384': 384, 'SHA3-384': 384, 'SHA-0': 160,
        'SHA-512': 512, 'SHA3-512': 512, 'SHA-1': 160,
    }

    name = 'bit_length'

    def convert(self, value: Any, param: Parameter | None, ctx: Context | None) -> Any:
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

    def shell_complete(self, ctx: Context, param: Parameter, incomplete: str) -> list[CompletionItem]:
        algorithms = self.ALGORITHMS.keys()
        algorithms = filter(lambda a: a.startswith(incomplete), algorithms) if incomplete else algorithms
        algorithms = tuple(algorithms)
        assert algorithms
        return [CompletionItem(a) for a in algorithms]


@command('randbits')
@argument('bits', type=BitLength())
@option('-q', '--qty', type=int, default=10, help='输出多少串bytes（每行一串）。')
@option('-x', '--hex', 'hexadecimal', is_flag=True, help='以十六进制字节格式输出。（默认）')
@option('-d', '--dec', 'decimal', is_flag=True, help='以十进制字节格式输出。')
@option('-i', '--int', 'integer', is_flag=True, help='以整数形式输出。')
@option('--seperator', default='', help='每组之间的间隔符。')
@option('--prefix', default='', help='每组字节的前缀。')
@option('--suffix', default='', help='每组字节的后缀。')
@option('--head', default='', help='开头的前缀。')
@option('--tail', default='', help='结尾的尾缀。')
@option('--group', default=1, type=int, help='多少字节一组（默认1）。')
def generate_bits(
        bits, qty, hexadecimal, decimal, integer, group,
        seperator, prefix, suffix, head, tail
):
    """随机生成 qty 个 BITS 比特的字节串。"""
    if integer:
        op = None
    elif decimal:
        op = DecBytes(seperator, prefix, suffix, head, tail)
    else:
        op = HexBytes(seperator, prefix, suffix, head, tail, group)

    qb = ceil(bits / 8)  # quantity of bytes
    ds = (getrandbits(bits) for _ in range(qty))
    ds = (op.encode(d.to_bytes(qb, 'little')) for d in ds) if op else (str(d) for d in ds)
    print('\n'.join(ds))
