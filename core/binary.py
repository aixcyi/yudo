__all__ = [
    'BinaryEncoderAbc',
    'HexBinaryEncoder',
    'DecBinaryEncoder',
    'BaseBinaryEncoder',
    'PythonicBinaryEncoder',
]

from base64 import b64encode, b85encode, b32encode
from typing import Final


class BinaryEncoderAbc(object):

    def encode(self, data: bytes | bytearray) -> str:
        raise NotImplementedError()


class HexBinaryEncoder(BinaryEncoderAbc):
    def __init__(self,
                 bytes_per_sep: int = 1,
                 seperator: str = '',
                 prefix: str = '',
                 suffix: str = '',
                 head: str = '',
                 tail: str = '', ):
        self.bytes_per_sep = bytes_per_sep
        self.seperator = seperator
        self.prefix = prefix
        self.suffix = suffix
        self.head = head
        self.tail = tail
        if bytes_per_sep == 0:
            raise ValueError(
                'See parameter "bytes_per_sep" of bytes.hex() in package builtins.'
                '间隔符前后的字节数，正数从前往后数，负数从后往前数，唯独不能为0。'
            )

    def encode(self, data) -> str:
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


class DecBinaryEncoder(BinaryEncoderAbc):
    def __init__(self,
                 seperator: str = ',',
                 prefix: str = '',
                 suffix: str = '',
                 head: str = '',
                 tail: str = '', ):
        self.seperator = seperator
        self.prefix = prefix
        self.suffix = suffix
        self.head = head
        self.tail = tail
        if not seperator:
            raise ValueError(
                'Cannot ignore seperator when you translate to decimal format.'
                '将binary转换为基于非十六进制的字符串时，间隔符不能不填。'
            )

    def encode(self, data) -> str:
        mid = (f'{self.prefix}{byte:i}{self.suffix}' for byte in data)
        return self.head + self.seperator.join(mid) + self.tail


class BaseBinaryEncoder(BinaryEncoderAbc):
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


class PythonicBinaryEncoder(HexBinaryEncoder):
    # b"\xd7\xd3\xd2\xed"

    def __init__(self):
        super().__init__(prefix=r'\x', head=r'b"', tail='"')
