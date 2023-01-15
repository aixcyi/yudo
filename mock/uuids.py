__all__ = [
    'UUIDType',
    'UUIDMock',
]

from enum import IntEnum
from uuid import uuid4

from mock.basic import Mock


class UUIDType(IntEnum):
    UUID = 1
    HEX = 2
    INT = 3
    URN = 4


class UUIDMock(Mock):
    def __init__(self, types: UUIDType):
        self._type = types

    def mock(self, cycle, *args, **kwargs):
        match self._type:
            case UUIDType.UUID:
                ds = (str(uuid4()) for _ in cycle)
            case UUIDType.HEX:
                ds = (uuid4().hex for _ in cycle)
            case UUIDType.INT:
                ds = (str(uuid4().int) for _ in cycle)
            case UUIDType.URN:
                ds = (uuid4().urn for _ in cycle)
            case _:
                raise ValueError
        self._dataset = ds
        return self
