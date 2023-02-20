import os
import re
from pathlib import Path
from typing import NoReturn

import click
from rich import box
from rich.console import Console
from rich.table import Table

from core.click_chore import YudoConfigs, AutoReadConfigPaser, cmd, ask
from core.style import *
from .configurator import configurate


def get_cfp(short_name='', prefix='frpc') -> Path | None:
    """
    获取frpc或frps的配置文件的地址。

    :param short_name: 短名称。指的是文件名中 frpc_{full}.ini 的括号部分，如果不提供则表示 frpc.ini。
    :param prefix: 前缀。指的是 {frpc}_full.ini 的括号部分。必须是 frpc 或 frps。
    :return:
    """
    # 查找frp的安装目录
    with YudoConfigs() as configs:
        try:
            path = Path(configs['frp']['path'])
        except KeyError:
            click.secho('未设置frp的安装目录。可以使用以下命令设置：\n' +
                        cmd(configurate, 'frp.path=YOUR_INSTALL_PATH'),
                        err=True, fg=PT_WARNING)
            return None
        if not path.is_dir():
            click.secho('设置的不是一个目录。请使用以下命令修改frp安装目录：\n' +
                        cmd(configurate, 'frp.path=YOUR_INSTALL_PATH'),
                        err=True, fg=PT_WARNING)
            return None
        if not path.exists():
            click.secho('设置的frp安装目录不存在。请使用以下命令重新设置：\n' +
                        cmd(configurate, 'frp.path=YOUR_INSTALL_PATH'),
                        err=True, fg=PT_WARNING)
            return None

    # 在frp安装目录中拼接配置文件的地址
    # 并校验文件存在和属性
    cfp = path / (f'{prefix}_{short_name}.ini' if short_name else f'{prefix}.ini')
    if not cfp.exists():
        if not ask(f'配置文件 {cfp!s} 不存在。\n是否创建？(Y/[n]) '):
            return None
        cfp.touch()
    if not cfp.is_file():
        click.secho(f'路径 {cfp!s} 不是一个文件。', err=True, fg=PT_WARNING)
        return None

    return cfp


def list_configs(prefix: str, manger, getter) -> NoReturn:
    """
    列出 frpc 或 frps 的所有配置文件。

    :param prefix: 配置文件名前缀。只能是“frpc”和“frps”。
    :param manger: 管理配置的命令。用于合成命令行展示。
    :param getter: 查询配置的子命令。用于合成命令行展示。
    :return: 无。
    """
    if not (cfp := get_cfp(prefix=prefix)):
        return

    table = Table('简短名称', '文件名称', '查看方式', box=box.SIMPLE_HEAD)
    for d in cfp.parent.iterdir():
        result = re.fullmatch(prefix + r'_?(.*)\.ini', d.name)
        if not result:
            continue
        if name := result.group(1):
            command = cmd(manger, getter, '-c', name)
        else:
            command = cmd(manger, getter)
        table.add_row(name, d.name, command)
    else:
        console = Console()
        console.print(table)


def set_config(prefix: str, filename: str, pattern: str) -> NoReturn:
    """
    查询或修改 frpc 或 frps 的配置文件。

    :param prefix: 配置文件名前缀。只能是“frpc”和“frps”。
    :param filename: 配置的简短名称。例如 “full” 代表 “frpc_full.ini”。
    :param pattern: 符合表达式 [SECTION[.KEY[=VALUE]]] 的用户输入。
    :return: 无。
    """
    if not (cfp := get_cfp(filename, prefix)):
        return
    section, key, value = AutoReadConfigPaser.parse_path(pattern)

    with AutoReadConfigPaser(cfp, auto_patch=True) as configs:
        # 打印整个配置文件
        if not section:
            configs.print_all(nl=True)
            return

        if not configs.check_section(section):
            return

        # 打印一整个section
        if not key:
            configs.print_section(section)
            return

        if not configs.check_key(section, key):
            return

        # 打印具体配置
        if not value:
            click.secho(configs[section][key])
            return

        configs[section][key] = value
        configs.save()


def run_frp(prefix: str, filename: str, new_configs: tuple[str], print_it: bool) -> NoReturn:
    """
    运行 frpc 或 frps 程序。

    :param prefix: 配置文件名前缀。只能是“frpc”和“frps”。
    :param filename: 配置的简短名称。例如 “full” 代表 “frpc_full.ini”。
    :param new_configs: 多个符合表达式 [SECTION[.KEY[=VALUE]]] 的用户输入。
    :param print_it: 保存后打印当前配置。
    :return: 无。
    """
    if not (cfp := get_cfp(filename, prefix=prefix)):
        return

    if new_configs:
        with AutoReadConfigPaser(cfp, auto_patch=True) as configs:
            for new_config in new_configs:
                section, key, value = AutoReadConfigPaser.parse_path(new_config)
                if not all([section, key, value]):
                    click.secho(f'配置格式无法解析。', err=True, fg=PT_WARNING)
                    return None
                configs[section][key] = value
                configs.save()

    if print_it:
        with AutoReadConfigPaser(cfp, auto_patch=True) as configs:
            configs.print_all()

    if prefix == 'frpc':
        os.execl(cfp.parent / 'frpc', 'http', '-c', str(cfp))
    elif prefix == 'frps':
        pass


@click.group('frpc', short_help='管理、配置、运行frp客户端（frpc）')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def manage_frpc():
    """
    管理、配置、运行frp客户端（frpc）。
    """


@manage_frpc.command('list', short_help='列出frpc所有配置')
def frpc_list_configs():
    list_configs('frpc', manage_frpc, frpc_set_configs)


@manage_frpc.command('set', short_help='查看或修改frpc的配置')
@click.argument('pattern', metavar='[SECTION[.KEY[=VALUE]]]', required=False)
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='要修改哪个配置文件，提供简短名称即可。比如 frpc_full.ini 的简短名称就是 full')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def frpc_set_configs(
        pattern: str | None, filename: str | None,
):
    """
    设置一个配置项，或者查看配置项。

    例如：
      - 打印文件："yu frpc set"
      - 打印某节："yu frpc set common"
      - 打印配置："yu frpc set common.server_port"
      - 修改配置："yu frpc set common.server_port=65535"

    默认围绕 frpc.ini 进行操作，假设要对  frpc_full.ini 操作，就需要附加 -c full 选项。
    """
    set_config('frpc', filename, pattern)


@manage_frpc.command('run', short_help='运行frpc')
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='用某个配置文件来运行。提供简短名称。使用 yu frpc conf -l 查看所有。')
@click.option('-s', '--set', 'new_configs', metavar='SECTION.KEY=VALUE',
              multiple=True, help='修改并保存配置后再运行。使用多个 -s 来修改多个配置。')
@click.option('-p', '-print', 'print_it', is_flag=True,
              help='运行前打印文件中的所有配置。')
def run_frpc(
        filename: str | None,
        new_configs: tuple[str] | None,
        print_it: bool,
):
    run_frp('frpc', filename, new_configs, print_it)


@click.group('frps', short_help='管理、配置、运行frp服务端（frps）')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def manage_frps():
    """
    管理、配置、运行frp服务端（frps）。
    """


@manage_frps.command('list', short_help='列出frps所有配置')
def frpc_list_configs():
    list_configs('frps', manage_frps, frps_set_configs)


@manage_frps.command('set', short_help='查看或修改frps的配置')
@click.argument('pattern', metavar='[SECTION[.KEY[=VALUE]]]', required=False)
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='要修改哪个配置文件，提供简短名称即可。比如 frps_full.ini 的简短名称就是 full')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def frps_set_configs(
        pattern: str | None, filename: str | None,
):
    """
    设置一个配置项，或者查看配置项。

    例如：
      - 打印文件："yu frps set"
      - 打印某节："yu frps set common"
      - 打印配置："yu frps set common.server_port"
      - 修改配置："yu frps set common.server_port=65535"

    默认围绕 frpc.ini 进行操作，假设要对  frpc_full.ini 操作，就需要附加 -c full 选项。
    """
    set_config('frps', filename, pattern)


@manage_frps.command('run', short_help='运行frps')
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='用某个配置文件来运行。提供简短名称。使用 yu frps list 查看所有。')
@click.option('-s', '--set', 'new_configs', metavar='SECTION.KEY=VALUE',
              multiple=True, help='修改并保存配置后再运行。使用多个 -s 来修改多个配置。')
@click.option('-p', '-print', 'print_it', is_flag=True,
              help='运行前打印文件中的所有配置。')
def run_frpc(
        filename: str | None,
        new_configs: tuple[str] | None,
        print_it: bool,
):
    run_frp('frps', filename, new_configs, print_it)
