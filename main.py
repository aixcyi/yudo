r"""
                    __
   __  ____  ______/ /___
  / / / / / / / __  / __ \
 / /_/ / /_/ / /_/ / /_/ /
 \__, /\__,_/\__,_/\____/
/____/
"""
import sys
from importlib import import_module

from core.exceptions import BatchException

if __name__ == '__main__':
    # (main.py mock bin --hex ...)
    self, *argv = sys.argv
    if len(argv) == 0:
        print(__doc__)
        sys.exit(0)

    # (mock bin --hex ...)
    instruction, *args = argv
    try:
        package = import_module(instruction)
    except ImportError:
        print(__doc__)
        sys.exit(0)

    # (bin --hex ...)
    if not hasattr(package, 'paser'):
        print(f'请在模块 {package.__name__} 的 __init__.py 中'
              '添加一个 paser=argpase.ArgumentParser()', file=sys.stderr)
        sys.exit(-10086)
    namespace = package.paser.parse_args(args if args else ['-h'])
    if hasattr(package, 'maps') and namespace.operation in package.maps:
        op = package.maps[namespace.operation]
    else:
        op = namespace.operation
    subpackage = import_module(f'{instruction}.{op}')
    try:
        subpackage.main(namespace)
    except BatchException as e:
        e.stop()

# @staticmethod
# def time(namespace, cycle):
#     worker = DatetimeMock.near_mode(
#         types=namespace.types,
#         mode=namespace.mode,
#         delta=str2delta(namespace.delta),
#     )
#     worker.fmt = namespace.format if namespace.format else worker.fmt
#     worker.mock(cycle).pprint()
#
# @staticmethod
# def uuid(namespace, cycle):
#     worker = UUIDMock(namespace.types)
#     worker.mock(cycle).pprint()
#
# @staticmethod
# def ipv4(namespace, cycle):
#     if namespace.network:
#         try:
#             worker = IPv4AddressMock.network_mode(namespace.network)
#         except (ValueError, TypeError, OverflowError) as e:
#             raise OperatingException(msg=str(e))
#     else:
#
#         worker = IPv4AddressMock(start, stop)
#     worker.mock(cycle).pprint()
#
# @staticmethod
# def ipv6(namespace, cycle):
#     worker = IPv6AddressMock()
#     worker.mock(cycle, namespace.compatible)
#     worker.pprint()
#
# # @staticmethod
# # def id(namespace, cycle):
# #     t = (namespace.male, namespace.female)
# #     gender = 'Male' if t == (True, False) else 'Female' if t == (False, True) else 'Both'
# #     bits = 15 if namespace.old else 18
# #     age_min = namespace.min if namespace.min else 0
# #     age_max = namespace.max if namespace.max else 70
# #     provinces = namespace.province if namespace.province else PROVINCES
# #     cities = ()
# #     counties = ()
# #
# #     results = (make_id() for _ in cycle)
# #     print('\n'.join(results))
