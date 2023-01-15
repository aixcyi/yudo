import sys
from typing import Any, NoReturn


class Mock(object):
    _dataset = ()

    def check(self, *args, **kwargs):
        """检查或修正参数。"""
        return self

    def mock(self, cycle, *args, **kwargs):
        """
        生成模拟数据。
        """
        self._dataset = ()
        return self

    def want(self, *args, **kwargs) -> Any:
        """
        将数据处理为可用／可枚举的格式并返回。
        """
        return tuple(self._dataset)

    def output(self, *args, **kwargs) -> Any:
        """
        将数据处理为可打印的格式并返回。
        """
        return self._dataset

    def pprint(self, file=sys.stdout) -> NoReturn:
        """
        将数据打印到指定的文件（默认为标准输出流），并自动换行。
        """
        print('\n'.join(self.output()), file=file)


class MockingException(Exception):
    def __init__(self, msg='', *args, **kwargs):
        self.message = msg.format(*args, **kwargs)

    def __str__(self):
        return self.message


def get_cycle(namespace):
    return range(namespace.qty)
