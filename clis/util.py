from typing import NamedTuple
from urllib.parse import urlsplit, parse_qs

import click
import rich
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text


class NetLocation(NamedTuple):
    location: str
    port: int
    user: str
    password: str

    def is_pure(self) -> bool:
        return not (self.port and self.user and self.password)

    def is_default_port(self) -> bool:
        return self.port == 0

    def is_no_pwd(self) -> bool:
        return not self.password


def parse_loc(location: str):
    usr_part, _, loc_part = location.rpartition('@')
    loc, _, port = loc_part.partition(':')
    usr, _, pwd = (usr_part if loc_part else '').partition(':')
    return NetLocation(loc, port if port.isdigit() else 0, usr, pwd)


def beautify_list(values):
    if (qty := len(values)) == 0:
        return ""
    elif qty == 1:
        return values[0]
    else:
        s = ", ".join(values)
        return f'array({s})'


@click.command('url')
@click.option('-e', '--encoding', default='UTF-8', help='用何种编码解析。默认是UTF-8。')
@click.option('-l', '--parse-location', is_flag=True, help='是否解析域名部分。')
@click.option('-f', '--skip-fragment', is_flag=True,
              help='禁止解析片段部分。当#出现在URL路径中导致结果错误时使用，但可能导致query受污染。')
@click.help_option('-h', '--help')
def split_url(encoding, parse_location, skip_fragment):
    """解析一条URL。"""
    click.secho('输入一条URL：', err=True, nl=False)
    info = urlsplit(input(), allow_fragments=not skip_fragment)._asdict()

    match info['scheme']:
        case 'https':
            info['scheme'] = Text(info['scheme'], Style(color='green'))

    location = parse_loc(info['netloc'])
    if not location.is_pure() and parse_location:
        info['netloc'] = Table('Property', 'Content', box=None, show_header=False)
        for k, v in location._asdict().items():
            info['netloc'].add_row(k, v)

    queryset = parse_qs(info['query'], encoding=encoding) if info['query'] else None
    if queryset:
        info['query'] = Table('Key', 'Value', box=None)
        for k, v in queryset.items():
            info['query'].add_row(k, beautify_list(v))

    table = Table('Property', 'Content', box=rich.box.SIMPLE_HEAD)
    for attr, value in info.items():
        table.add_row(attr, value)
    Console().print(table)
