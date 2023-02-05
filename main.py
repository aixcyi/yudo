r"""
                    __
   __  ____  ______/ /___
  / / / / / / / __  / __ \
 / /_/ / /_/ / /_/ / /_/ /
 \__, /\__,_/\__,_/\____/
/____/
         "Python 3.10 powerful script."
"""
__version__ = (0, 1, 0, 'release', 0xd2ed)
__author__ = 'aixcyi'

import typing

import click
import rich

from clis import interface_list

interfaces = []
interfaces += interface_list


@click.group()
@click.help_option('-h', '--help')
@click.version_option('.'.join(map(str, __version__)), '-v', '--version', message='%(version)s')
def cli():
    pass


def get_help(self: click.Context) -> typing.NoReturn:
    info = self.to_info_dict()['command']['commands']
    table = rich.table.Table('', '', box=None)
    for n, h in info.items():
        if h['deprecated']:
            n = rich.text.Text(n, rich.style.Style(color='bright_blue'))
        table.add_row(n, h["help"])
    table.add_row('-v', '查看yudo的版本号。')
    table.add_row('-h', '查看yudo的帮助信息。')

    console = rich.console.Console()
    console.print(__doc__)
    console.print(table)


if __name__ == '__main__':
    for i in interfaces:
        cli.add_command(i)
    cli.get_help = get_help
    cli()
