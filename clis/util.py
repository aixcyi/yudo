from typing import NamedTuple
from urllib.parse import urlsplit, parse_qs, quote_plus, quote, unquote, unquote_plus

import click
from rich import box
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from core.click_chore import YudoConfigs
from core.style import *


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


@click.command('url', short_help='解析一条URL')
@click.option('-e', '--encoding', default='UTF-8', help='用何种编码解析。默认是UTF-8。')
@click.option('-l', '--parse-location', is_flag=True, help='是否解析域名部分。')
@click.option('-f', '--skip-fragment', is_flag=True,
              help='禁止解析片段部分。当#出现在URL路径中导致结果错误时使用，但可能导致query受污染。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def split_url(encoding, parse_location, skip_fragment):
    """
    请求输入并解析一条URL。支持http、ftp等等相似格式的字符串。
    """
    click.secho('输入一条URL：', err=True, nl=False)
    info = urlsplit(input(), allow_fragments=not skip_fragment)._asdict()

    match info['scheme']:
        case 'https':
            info['scheme'] = Text(info['scheme'], Style(color=URL_SECURITY_PROTOCOL))

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

    table = Table('Property', 'Content', box=box.SIMPLE_HEAD)
    for attr, value in info.items():
        table.add_row(attr, value)
    Console().print(table)


@click.command('urlen', short_help='对字符串进行URL编码')
@click.option('-p', '--plus', is_flag=True, help="将空格转义为 + 号，而不是直接编码为 %20 。")
@click.option('-e', '--encoding', default='UTF-8', help="字符编码，默认是 UTF-8。")
@click.option('-s', 'safes', default='', help="不允许转码的字符。默认没有。")
def encode_uri(plus: bool, encoding: str, safes: str):
    """
    对字符串进行URL编码。
    """
    click.secho('输入任意字符串：', err=True, nl=False)
    translate = quote_plus if plus else quote
    print(translate(input(), safe=safes, encoding=encoding))


@click.command('urlde', short_help='将字符串按照URL编码规则来解码')
@click.option('-p', '--plus', is_flag=True, help="将 + 号转义为空格。")
@click.option('-e', '--encoding', default='UTF-8', help="字符编码，默认是 UTF-8。")
def decode_uri(plus: bool, encoding: str):
    """
    将字符串按照URL编码规则来解码。
    """
    click.secho('输入任意字符串：', err=True, nl=False)
    translate = unquote_plus if plus else unquote
    print(translate(input(), encoding=encoding))


@click.command('len', short_help='测量输入文本的字符数和字节数')
@click.option('-e', '--encoding', default='UTF-8', help='用何种编码转换文本。默认是UTF-8。')
def get_length(encoding: str):
    """
    获取输入文本的字符数和字节数。
    """
    click.secho('字符串：', err=True, nl=False, fg=PT_INPUT_TIP)
    text = input()
    try:
        binary = text.encode(encoding=encoding)
    except LookupError:
        click.secho(f'无法将字符串转换到 {encoding} 编码。', err=True, fg=PT_WARNING)
        return
    print(f'字符数：{len(text)}')
    print(f'字节数：{len(binary)}（{encoding}）')
    print(f'比特数：{len(binary)*8}')
