import re
import typing
from configparser import ConfigParser
from io import StringIO
from pathlib import Path
from typing import Pattern

import click
from click import ParamType, secho, echo
from rich import box
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from core.style import *

cfp = Path(__file__).parent.parent / 'yudo.ini'


def fmt_datasize(size: int) -> str:
    if size < 1024:
        return f'{size:d} Bytes'
    elif size < 1024 ** 2:
        return f'{size / 1024:.2f} KB'
    elif size < 1024 ** 3:
        return f'{size / 1024 ** 2:.2f} MB'
    elif size < 1024 ** 4:
        return f'{size / 1024 ** 3:.2f} GB'
    else:
        return f'{size / 1024 ** 4:.2f} TB'


class Regex(ParamType):
    name = 'regex'

    def convert(self, value: str, param, ctx) -> Pattern:
        try:
            return re.compile(value)
        except re.error:
            self.fail('正则表达式有误。', param, ctx)


def ask(dateset, force: bool) -> bool:
    qty = len(dateset)
    dsz = fmt_datasize(len(dateset[0]) * qty if dateset else 0)
    tip = f'预估数据量 {qty:d} 条，文本 {dsz}，确定继续？(Y/[n]) '
    if qty == 0:
        secho('没有产生任何数据。', err=True, fg=PT_WARNING)
        return False
    if force is False:
        echo(tip, err=True, nl=False)
        if input()[:1] != 'Y':
            return False
    return True


class YuConfiguration(ConfigParser):
    save_finally = False

    def __enter__(self):
        self.read(cfp, encoding='UTF-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.save_finally:
            with open(cfp, 'w', encoding='UTF-8') as f:
                self.write(f)

    def get(self, section: str, option: str, *, raw=False, vars=None, fallback=object()) -> str:
        value = super().get(section, option, raw=raw, vars=vars, fallback=fallback)
        if section == 'charset':
            try:
                value = str(bytes.fromhex(value), encoding='ASCII')
            except ValueError:
                click.secho('charset 的配置值解码失败。', err=True, fg=PT_ERROR)
                exit(-1)
        return value

    def set(self, section: str, option: str, value: str | None = ...) -> None:
        if section == 'charset':
            try:
                value = bytes(value, encoding='ASCII').hex()
            except ValueError:
                click.secho('charset 的配置值不能含有非ASCII字符。', err=True, fg=PT_ERROR)
                exit(-1)
        return super().set(section, option, value)

    def gettext(self):
        with StringIO() as f:
            self.write(f)
            return f.getvalue()

    def ensure(self, section: str):
        if section not in self:
            self.add_section(section)
        return self[section]


def get_help(self: click.Context) -> typing.NoReturn:
    info = self.to_info_dict()['command']['commands']
    table = Table('Command', 'Description', box=box.SIMPLE_HEAD, row_styles=MT_ROW)
    for n, h in info.items():
        if h['deprecated']:
            n = Text(n, Style(color=MT_DEPRECATED))
        table.add_row(n, h['short_help'])
    table.add_row('-v', '查看yudo的版本号')
    table.add_row('-h', '查看此帮助信息')

    console = Console()
    console.print(get_help.__doc__)
    console.print(table)
