r"""
                    __
   __  ____  ______/ /___
  / / / / / / / __  / __ \
 / /_/ / /_/ / /_/ / /_/ /
 \__, /\__,_/\__,_/\____/
/____/
         Python 3.10 powerful script.
"""
import typing

import click

from clis.adcode import get_adcode
from clis.arrangement import product_columns
from clis.binary import generate_bits
from clis.datetime import generate_date, generate_datetime
from clis.idcard import generate_prcid


@click.group()
def cli():
    pass


def get_help(self: click.Context) -> typing.NoReturn:
    print(__doc__)
    info = self.to_info_dict()['command']['commands']
    for k, v in info.items():
        print(f'{k:12s} {v["help"]}')


if __name__ == '__main__':
    cli.add_command(get_adcode)
    cli.add_command(generate_bits)
    cli.add_command(generate_date)
    cli.add_command(generate_datetime)
    cli.add_command(generate_prcid)
    cli.add_command(product_columns)
    cli.get_help = get_help
    cli()
