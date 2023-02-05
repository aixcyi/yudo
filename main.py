r"""
                    __
   __  ____  ______/ /___
  / / / / / / / __  / __ \
 / /_/ / /_/ / /_/ / /_/ /
 \__, /\__,_/\__,_/\____/
/____/
         "Python 3.10 powerful script."
"""
__version__ = (0, 1, 'release', 0xd2ed)
__author__ = 'aixcyi'

import typing

import click
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from clis.adcode import get_adcode
from clis.binary import generate_bits
from clis.datetime import enum_date, enum_datetime
from clis.idcard import enum_prcid
from clis.sequence import product_columns
from clis.util import split_url


@click.group()
def cli():
    pass


def get_help(self: click.Context) -> typing.NoReturn:
    info = self.to_info_dict()['command']['commands']
    table = Table('', '', box=None)
    for n, h in info.items():
        if h['deprecated']:
            table.add_row(Text(n, Style(color='bright_blue')), h["help"])
        else:
            table.add_row(n, h["help"])

    console = Console()
    console.print(__doc__)
    console.print(table)


if __name__ == '__main__':
    cli.add_command(get_adcode)
    cli.add_command(generate_bits)
    cli.add_command(enum_date)
    cli.add_command(enum_datetime)
    cli.add_command(enum_prcid)
    cli.add_command(product_columns)
    cli.add_command(split_url)
    cli.get_help = get_help
    cli()
