r"""
                      __
     __  ____  ______/ /___
    / / / / / / / __  / __ \
   / /_/ / /_/ / /_/ / /_/ /
   \__, /\__,_/\__,_/\____/
  /____/
          "Python 3.10 easiest customizable script."
"""
__version__ = (0, 1, 0, 0xd2ed, 'release')
__author__ = 'aixcyi'

import click

import clis
from core.click_chore import get_help

interfaces = []
interfaces += clis.interface_list


@click.group('yu', commands=interfaces)
@click.help_option('-h', '--help')
@click.version_option('.'.join(map(str, __version__)), '-v', '--version', message='%(version)s')
def cli():
    pass


if __name__ == '__main__':
    get_help.__doc__ = __doc__
    cli.get_help = get_help
    cli()
