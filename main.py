r"""
                    __
   __  ____  ______/ /___
  / / / / / / / __  / __ \
 / /_/ / /_/ / /_/ / /_/ /
 \__, /\__,_/\__,_/\____/
/____/
         Python 3.10 powerful script.
"""
import click

from clis.binary import randbits
from clis.idcard import enumidc


@click.group()
def cli():
    pass


if __name__ == '__main__':
    cli.add_command(randbits)
    cli.add_command(enumidc)
    cli.get_help = lambda ctx: print(__doc__)
    cli()
