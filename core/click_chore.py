import re
import typing
from configparser import ConfigParser, SectionProxy
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


class PortableConfiguration(ConfigParser):

    def __init__(self, cfp, save_finally=False, auto_section=False, *args, **kwargs):
        self.cfp = cfp
        self.save_finally = save_finally
        self.auto_section = auto_section
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: str) -> SectionProxy:
        if key != self.default_section and not self.has_section(key):
            if self.auto_section:
                self.__setitem__(key, {})
            else:
                raise KeyError(key)
        return self._proxies[key]

    def __enter__(self):
        self.read(self.cfp, encoding='UTF-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.save_finally:
            with open(self.cfp, 'w', encoding='UTF-8') as f:
                self.write(f)

    def ensure(self, section: str):
        if section not in self:
            self.add_section(section)
        return self[section]

    def gettext(self):
        with StringIO() as f:
            self.write(f)
            return f.getvalue()

    def print_all(self, nl=False):
        for title, section in self.items():
            if title == 'DEFAULT':
                continue
            click.secho('[', fg=PT_CONF_SECTION, nl=False)
            click.secho(title, nl=False)
            click.secho(']', fg=PT_CONF_SECTION)
            for _key in section:
                click.secho(_key, fg=PT_CONF_KEY, nl=False)
                click.secho('=', fg=PT_CONF_EQU, nl=False)
                click.secho(section[_key])
            else:
                if nl is True:
                    click.echo()

    def print_section(self, section: SectionProxy | str):
        if isinstance(section, str):
            section = self[section]
        elif isinstance(section, SectionProxy):
            pass
        else:
            raise TypeError()

        for k in section:
            click.secho(k, nl=False, fg=PT_CONF_KEY)
            click.secho(' = ', nl=False, fg=PT_CONF_EQU)
            click.secho(section[k])

    def curd(self, section: str = '', key: str = '', value: str | None = None):
        # 枚举所有节
        if not section:
            self.print_all(nl=True)

        # 枚举一整节
        elif section and not key:
            if section not in self:
                click.secho(f'找不到 {section} 。', err=True, fg=PT_WARNING)
                click.secho('注意：节名称是区分大小写的。', err=True, fg=PT_SPECIAL)
                return
            self.print_section(section)

        # 打印某个配置项
        elif section and key and value is None:
            if section not in self:
                click.secho(f'找不到 {section} 。', err=True, fg=PT_WARNING)
                return
            if key not in self[section]:
                click.secho(f'找不到 {section} 下的 {key}。', err=True, fg=PT_WARNING)
                return
            click.secho(self[section][key])

        # 设置配置值
        elif section and key and value is not None:
            self.save_finally = True
            self.ensure(section)[key] = value


class YuConfiguration(PortableConfiguration):

    def __init__(self, *args, **kwargs):
        cfp = Path(__file__).parent.parent / 'yudo.ini'
        super().__init__(cfp, *args, **kwargs)

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


def get_help(self: click.Context) -> typing.NoReturn:
    commands = self.to_info_dict()['command']['commands']
    table = Table('Command', 'Description', box=box.SIMPLE_HEAD, row_styles=MT_ROW)
    for name, info in commands.items():
        if info['hidden']:
            continue
        if info['deprecated']:
            name = Text(name, Style(color=MT_DEPRECATED))
        table.add_row(name, info['short_help'])
    table.add_row('-v', '查看yudo的版本号')
    table.add_row('-h', '查看此帮助信息')

    console = Console()
    console.print(get_help.__doc__)
    console.print(table)
