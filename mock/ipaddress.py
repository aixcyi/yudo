__all__ = [
    'IPv4AddressMock',
    'IPv6AddressMock',
]

import re
from random import randbytes, randint
from ipaddress import IPv4Address

from mock.basic import Mock


class IPv4AddressMock(Mock):

    @classmethod
    def network_mode(cls, network: IPv4Address, mask: int):
        net = int(network)
        start = net & mask
        stop = start | (~mask & 0xFFFF_FFFF)
        return cls(IPv4Address(start), IPv4Address(stop))

    def __init__(self, start: IPv4Address, stop: IPv4Address):
        self._start = int(start)
        self._stop = int(stop)

    def mock(self, cycle, *args, **kwargs):
        ds = (randint(self._start, self._stop) for _ in cycle)
        self._dataset = ds
        return self

    def want(self, *args, **kwargs):
        return map(IPv4Address, self._dataset)

    def output(self, *args, **kwargs):
        return map(str, self.want(*args, **kwargs))


class IPv6AddressMock(Mock):

    @staticmethod
    def b2s(ip: bytes) -> str:
        string = ':'.join((
            ip[:2].hex().lstrip('0'), ip[2:4].hex().lstrip('0'),
            ip[4:6].hex().lstrip('0'), ip[6:8].hex().lstrip('0'),
            ip[8:10].hex().lstrip('0'), ip[10:12].hex().lstrip('0'),
            ip[12:14].hex().lstrip('0'), ip[14:16].hex().lstrip('0'),
        ))
        string = re.sub(r':{2,}', '--', string, count=1)
        while string.find('::') > 0:
            string = string.replace('::', ':0:')
        return string.replace('--', '::')

    @staticmethod
    def b2sc(ip: bytes) -> str:
        string = '{0}:{1}:{2}:{3}:{4}:{5}:{6}.{7}.{8}.{9}'.format(
            ip[:2].hex().lstrip('0'), ip[2:4].hex().lstrip('0'),
            ip[4:6].hex().lstrip('0'), ip[6:8].hex().lstrip('0'),
            ip[8:10].hex().lstrip('0'), ip[10:12].hex().lstrip('0'),
            *ip[12:16],
        )
        string = re.sub(r':{2,}', '--', string, count=1)
        while string.find('::') > 0:
            string = string.replace('::', ':0:')
        return string.replace('--', '::', 1)

    def mock(self, cycle, compatible=False, *args, **kwargs):
        ds = (randbytes(16) for _ in cycle)
        ds = map(self.b2sc if compatible else self.b2s, ds)
        self._dataset = ds
        return self
