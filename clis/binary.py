import math
import random
from typing import Final, Any

import click
from click import ParamType, Parameter, Context

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


@click.command(help='随机生成 qty 个字节串。')
@click.argument('bits', type=BitLength())
@click.option('-q', '--qty', type=int, default=10, help='输出多少串bytes（每行一串）。')
@click.option('-x', '--hex', is_flag=True, help='以十六进制字节格式输出。（默认）')
@click.option('-d', '--dec', is_flag=True, help='以十进制字节格式输出。')
@click.option('-i', '--int', is_flag=True, help='以整数形式输出。')
@click.option('--seperator', default='', help='每组之间的间隔符。')
@click.option('--prefix', default='', help='每组字节的前缀。')
@click.option('--suffix', default='', help='每组字节的后缀。')
@click.option('--head', default='', help='开头的前缀。')
@click.option('--tail', default='', help='结尾的尾缀。')
@click.option('--group', default=1, type=int, help='多少字节一组（默认1）。')
def randbits(bits, qty, hex, dec, int, group,
             seperator, prefix, suffix, head, tail):
    if int:
        op = None
    elif dec:
        op = DecBytes(seperator, prefix, suffix, head, tail)
    else:
        op = HexBytes(seperator, prefix, suffix, head, tail, group)

    qb = math.ceil(bits / 8)  # quantity of bytes
    ds = (random.getrandbits(bits) for _ in range(qty))
    ds = (op.encode(d.to_bytes(qb, 'little')) for d in ds) if op else (str(d) for d in ds)
    print('\n'.join(ds))
