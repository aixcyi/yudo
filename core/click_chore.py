import re
import typing
from configparser import ConfigParser, SectionProxy
from io import StringIO
from pathlib import Path

import click
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


class Regex(click.ParamType):
    name = 'regex'

    def convert(self, value: str, param, ctx) -> typing.Pattern:
        try:
            return re.compile(value)
        except re.error:
            self.fail('正则表达式有误。', param, ctx)


def warning(*line, nl=True, fg=PT_WARNING):
    click.secho('\n'.join(line), nl=nl, err=True, fg=fg)


def ask(tips: str = None, force: bool = False, dataset=None) -> bool:
    if dataset:
        qty = len(dataset)
        dsz = fmt_datasize(len(dataset[0]) * qty if dataset else 0)
        tip = tips if tips else f'预估数据量 {qty:d} 条，文本 {dsz}，确定继续？(Y/[n]) '
        if qty == 0:
            click.secho('没有产生任何数据。', err=True, fg=PT_WARNING)
            return False
        if force is False:
            click.echo(tip, err=True, nl=False)
            if input()[:1] != 'Y':
                return False
    else:
        tip = tips if tips else '是否继续？(Y/[n]) '
        click.secho(tip, err=True, nl=False, fg=PT_WARNING)
        if input()[:1] != 'Y':
            return False
    return True


class AutoReadConfigPaser(ConfigParser):

    @staticmethod
    def parse_path(pattern: str | None) -> tuple[str, str, str]:
        """
        按照表达式 [SECTION[.KEY[=VALUE]]] 解析输入值。

        默认允许 SECTION 包含 “.” 字符，而 KEY 不允许。

        :param pattern:
        :return: 返回 section，key，value 三个值。
        """
        if pattern is None:
            return '', '', ''
        _path, _, value = pattern.partition('=')
        section, _, key = _path.rpartition('.')
        if not section:
            section, key = key, ''
        return section, key, value

    def __init__(
            self, cfp, *args,
            auto_save=False,
            auto_patch=False,
            interpolation=None,
            encoding='UTF-8',
            **kwargs,
    ):
        """
        能够自动读取文件的配置文件解析器。

        :param cfp: 配置文件地址。
        :param auto_save: with 语句结束时自动保存。
        :param auto_patch: 访问 section 时，如果不存在则自动创建。
        :param interpolation: 不解析配置值中的引用写法。
        :param encoding: 文件编码。默认是 UTF-8 。
        :param args: ConfigParser 的位置参数。
        :param kwargs: ConfigParser 的命名参数。
        """
        self._cfp = cfp
        self._save = auto_save
        self._patch = auto_patch
        self._encoding = encoding
        super().__init__(*args, interpolation=interpolation, **kwargs)

    def __getitem__(self, key: str) -> SectionProxy:
        if key != self.default_section and not self.has_section(key):
            if self._patch:
                self.add_section(key)
            else:
                raise KeyError(key)
        return self._proxies[key]

    def __enter__(self):
        self.read(self._cfp, encoding=self._encoding)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._save:
            self.save()

    def save(self) -> typing.NoReturn:
        """
        保存到文件中。
        """
        with open(self._cfp, 'w', encoding='UTF-8') as f:
            self.write(f)

    def gettext(self) -> str:
        """
        获取当前配置的文本表示。
        """
        with StringIO() as f:
            self.write(f)
            return f.getvalue()

    def setdefaults(self, section: str, **kvs) -> typing.NoReturn:
        """
        设置多个默认值。

        :param section: 节名称。
        :param kvs: 键名称及默认值。
        """
        partition = self[section]
        for k, v in kvs.items():
            partition.setdefault(k, v)


class YudoConfigs(AutoReadConfigPaser):

    def __init__(self, *args, **kwargs):
        cfp = Path(__file__).parent.parent / 'yudo.ini'
        super().__init__(cfp, *args, **kwargs)

    def get(self, section: str, option: str, *, raw=False, variables=None, fallback=object()) -> str:
        value = super().get(section, option, raw=raw, vars=variables, fallback=fallback)
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

    table.add_row(Text('start', Style(color=MT_SPECIAL)), '切换到conda环境来使用yudo')
    table.add_row(Text('#install', Style(color=MT_SPECIAL)), '立刻安装yudo所需的pip包')
    table.add_row('-v', '查看yudo的版本号')
    table.add_row('-h', '查看此帮助信息')

    console = Console()
    console.print(get_help.__doc__)
    console.print(table)


def cmd(*args) -> str:
    return 'yu ' + ' '.join(
        arg.name if isinstance(arg, click.Command) else arg
        for arg in args
    )


def curd(parser, pattern: str, delete_it: bool):
    section, key, value = AutoReadConfigPaser.parse_path(pattern)

    with parser as configs:

        # 枚举所有节
        if not section:
            for title, section in configs.items():
                if title == configs.default_section:
                    continue
                click.secho('[', fg=PT_CONF_SECTION, nl=False)
                click.secho(title, nl=False)
                click.secho(']', fg=PT_CONF_SECTION)
                for _key in section:
                    click.secho(_key, fg=PT_CONF_KEY, nl=False)
                    click.secho('=', fg=PT_CONF_EQU, nl=False)
                    click.secho(section[_key])
                else:
                    click.echo()
            return

        if section not in configs:
            warning(f'找不到 {section} 。')
            warning('注意：节名称是区分大小写的。', fg=PT_SPECIAL)
            return

        # 枚举一整节
        if not key and not delete_it:
            for k in configs[section]:
                click.secho(k, nl=False, fg=PT_CONF_KEY)
                click.secho(' = ', nl=False, fg=PT_CONF_EQU)
                click.secho(configs[section][k])
            return

        # 删除一整节
        if not key and delete_it:
            if ask('确认删除一整节配置？(Y/[n]) '):
                configs.remove_section(section)
                configs.save()
            return

        if key not in configs[section]:
            warning(f'在 {section} 里找不到 {key}。')
            return

        # 打印一个配置项
        if not value and not delete_it:
            click.secho(configs[section][key])
            return

        # 删除一个配置项
        if not value and delete_it:
            if ask('是否确认删除？(Y/[n]) '):
                _ = configs[section].pop(key)
                configs.save()
            return

        # 设置配置值
        if section and key and value:
            configs.ensure(section)[key] = value
            configs.save()
