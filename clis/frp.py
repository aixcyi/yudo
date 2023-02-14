import os
import re
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.table import Table

from core.click_chore import YuConfiguration, PortableConfiguration
from core.style import *


def get_path():
    with YuConfiguration() as configs:
        try:
            path = Path(configs['frp']['path'])
        except KeyError:
            click.secho('在yudo的配置中没有找到frp的安装目录。', err=True, fg=PT_WARNING)
            return None
        if not path.is_dir():
            click.secho('配置的不是一个目录。', err=True, fg=PT_WARNING)
            return None
        if not path.exists():
            click.secho('配置的frp安装目录不存在。', err=True, fg=PT_WARNING)
            return None
    return path


def list_frpc_all_configs(root: Path):
    table = Table('配置文件', '查看方式', box=box.SIMPLE_HEAD)
    for directory in os.scandir(root):
        result = re.fullmatch(r'frpc_?(.*)\.ini', directory.name)
        if not result:
            continue
        name = result.group(1)
        table.add_row(directory.name, f'yu frpc conf -c {name}' if name else 'yu frpc conf')
    else:
        console = Console()
        console.print(table)


@click.group('frpc', short_help='管理、配置、运行frp客户端（frpc）')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def manage_frpc():
    """
    管理、配置、运行frp客户端（frpc）。

    使用前要先配置frp的安装目录，命令是 yu conf frp.path YOUR_PATH。
    """


@manage_frpc.command('conf', short_help='管理、设置frpc配置')
@click.argument('key', metavar='[SECTION[.KEY]]', default='', required=False)
@click.argument('value', required=False)
@click.option('-c', '--config', 'filename', metavar='NAME', help='查看或设置某个配置文件，提供简短名称。')
@click.option('-l', '--list', 'list_all', is_flag=True, help='列出所有配置文件。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def configurate(key: str, value: str | None, filename: str | None, list_all: bool):
    """
    设置单份frpc配置，管理多份frpc配置。
    """
    if not (path := get_path()):
        return
    if list_all:
        list_frpc_all_configs(path)
        return

    cfp = path / (f'frpc_{filename}.ini' if filename else 'frpc.ini')
    if not cfp.exists():
        click.secho(f'配置文件 {cfp!s} 不存在。\n是否创建？(Y/[n]) ', err=True, nl=False, fg=PT_WARNING)
        if input()[:0] != 'Y':
            return
        cfp.touch()
    if not cfp.is_file():
        click.secho(f'路径 {cfp!s} 不是一个文件。', err=True, fg=PT_WARNING)
        return None

    section, _, key = key.rpartition('.')
    if not section:
        section, key = key, ''

    with PortableConfiguration(cfp, auto_section=True, interpolation=None) as configs:
        configs.curd(section, key, value)


@manage_frpc.command('run', short_help='运行frp客户端')
@click.option('-c', '--config', 'filename', metavar='NAME', help='用某个配置文件来运行。提供简短名称。'
                                                                 '使用 yu frpc conf -l 查看所有。')
def run_frpc(filename: str | None):
    if not (path := get_path()):
        return
    cfp = path / (f'frpc_{filename}.ini' if filename else 'frpc.ini')
    if not cfp.is_file() or not cfp.exists():
        click.secho(f'找不到配置文件：{cfp!s}', err=True, fg=PT_WARNING)
        return None

    os.execl(path / 'frpc', 'http', '-c', str(cfp))
