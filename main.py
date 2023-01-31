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

from clis.binary import randbits
from clis.idcard import enumidc
from clis.datetime import gend, gendt


@click.group()
def cli():
    pass


def get_help(self: click.Context) -> typing.NoReturn:
    print(__doc__)
    info = self.to_info_dict()['command']['commands']
    for k, v in info.items():
        print(f'{k:12s} {v["help"]}')


if __name__ == '__main__':
    cli.add_command(randbits)
    cli.add_command(enumidc)
    cli.add_command(gend)
    cli.add_command(gendt)
    cli.get_help = get_help
    cli()
