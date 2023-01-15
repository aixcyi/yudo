import sys
from math import ceil
from random import getrandbits
from typing import Final

from core.binary import *
from core.exceptions import BatchException
from mock.basic import get_cycle

ALGORITHMS: Final = {
    'SM3': 256, 'MD2': 128, 'MD4': 128, 'MD5': 128,
    'SHA-224': 224, 'SHA3-224': 224, 'SHA-512/224': 224,
    'SHA-256': 256, 'SHA3-256': 256, 'SHA-512/256': 256,
    'SHA-384': 384, 'SHA3-384': 384, 'SHA-0': 160,
    'SHA-512': 512, 'SHA3-512': 512, 'SHA-1': 160,
}


def parse_bits(string: str):
    if string.isdecimal():
        return int(string)
    if string.endswith('B') and (bl := string[:-1]).isdecimal():
        return int(bl) * 8  # bytes_length * 8
    if string in ALGORITHMS.keys():
        return ALGORITHMS[string]
    raise BatchException(
        '没有给定或无法解析binary的长度。\n'
        '提示：长度只能是个不带符号的非零整数。\n'
        '如果需要填写算法名称，请从以下值挑选：\n' +
        ', '.join(sorted(ALGORITHMS.keys()))
    )


def main(namespace):
    cycle = get_cycle(namespace)
    bits = parse_bits(namespace.length)  # 每一行的比特数目
    if bits < 1:
        raise BatchException('binary长度无意义')
    bytes_per_sep = namespace.bpg if namespace.bpg else 1
    seperator = namespace.sep if namespace.sep else ''
    prefix = namespace.prefix if namespace.prefix else ''
    suffix = namespace.suffix if namespace.suffix else ''
    head = namespace.head if namespace.head else ''
    tail = namespace.tail if namespace.tail else ''

    if namespace.base:
        if namespace.base not in BaseBinaryEncoder.BASE_LIST:
            raise BatchException(
                f'不支持 Base{namespace.base} 编码。'
            )
        coder = BaseBinaryEncoder(namespace.base)
    elif namespace.hex_array:
        coder = HexBinaryEncoder(
            head=head, prefix=prefix, bytes_per_sep=bytes_per_sep,
            tail=tail, suffix=suffix, seperator=seperator,
        )
    elif namespace.dec_array:
        coder = DecBinaryEncoder(
            head=head, prefix=prefix,
            tail=tail, suffix=suffix, seperator=seperator,
        )
    else:
        coder = HexBinaryEncoder()

    dataset = (getrandbits(bits).to_bytes(ceil(bits / 8), 'little') for _ in cycle)
    dataset = map(coder.encode, dataset)
    print('\n'.join(dataset), file=sys.stdout)
