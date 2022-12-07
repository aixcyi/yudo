__all__ = [
    'parse_bits',
    'BinaryType',
    'BinaryMock',
]

from base64 import b64encode, b85encode, b32encode
from enum import IntEnum
from math import ceil
from random import getrandbits

from mocks.basic import Mock, MockingException


def parse_bits(string: str):
    if string.isdecimal():
        return int(string)
    if string.endswith('B') and (bl := string[:-1]).isdecimal():
        return int(bl) * 8  # bytes_length * 8
    if string in BinaryMock.ALGORITHMS.keys():
        return BinaryMock.ALGORITHMS[string]
    raise MockingException(
        '没有给定或无法解析binary的长度。\n提示：长度只能是个不带符号的非零整数。\n'
        '如果需要填写算法名称，请从以下值挑选：\n' +
        ', '.join(sorted(BinaryMock.ALGORITHMS.keys()))
    )


class BinaryType(IntEnum):
    HEX = 0x0100
    ARRAY_HEX = 0X0301
    ARRAY_DEC = 0X0302
    BASE = 0x0400
    BASE64 = BASE | 64
    BASE85 = BASE | 85
    BASE32 = BASE | 32


class BinaryMock(Mock):
    ALGORITHMS = {
        'SM3': 256, 'MD2': 128, 'MD4': 128, 'MD5': 128,
        'SHA-224': 224, 'SHA3-224': 224, 'SHA-512/224': 224,
        'SHA-256': 256, 'SHA3-256': 256, 'SHA-512/256': 256,
        'SHA-384': 384, 'SHA3-384': 384, 'SHA-0': 160,
        'SHA-512': 512, 'SHA3-512': 512, 'SHA-1': 160,
    }

    seperator = ','
    prefix = ''
    suffix = ''
    head = ''
    tail = ''

    def __init__(self, bits: int, encoding: BinaryType):
        self._bits = bits

        if encoding == BinaryType.HEX:
            self.mapper = lambda d: d.hex()
        elif encoding & BinaryType.BASE == BinaryType.BASE:
            match encoding:
                case BinaryType.BASE64:
                    self.mapper = lambda d: str(b64encode(d), encoding='ASCII')
                case BinaryType.BASE85:
                    self.mapper = lambda d: str(b85encode(d), encoding='ASCII')
                case BinaryType.BASE32:
                    self.mapper = lambda d: str(b32encode(d), encoding='ASCII')
                case _:
                    raise MockingException('这种 BaseN 不受支持。')
        else:
            if encoding == BinaryType.ARRAY_HEX:
                byte_map = lambda byte: f'{self.prefix}{byte:x}{self.suffix}'
            elif encoding == BinaryType.ARRAY_DEC:
                byte_map = lambda byte: f'{self.prefix}{byte:d}{self.suffix}'
            else:
                raise MockingException('错误的进位制。')
            self.mapper = lambda d: (
                    self.head +
                    self.seperator.join(map(byte_map, (byte for byte in d))) +
                    self.tail
            )

    def mock(self, cycle, *args, **kwargs):
        n = ceil(self._bits / 8)
        ds = (getrandbits(self._bits).to_bytes(n, 'little') for _ in cycle)
        self._dataset = map(self.mapper, ds)
        return self

    @staticmethod
    def map2array(binary):
        pass
