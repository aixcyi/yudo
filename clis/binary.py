from math import ceil
from random import getrandbits
from typing import Final, Any

import click
from click.shell_completion import CompletionItem

from core.binary import HexBytes, DecBytes, BaseBytes


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


@click.command('randbit')
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
def generate_bits(
        bits, qty, hexadecimal, decimal, integer, b64, b85, b32,
        group, seperator, prefix, suffix, head, tail
):
    """随机生成 BITS 比特的字节串。"""
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
