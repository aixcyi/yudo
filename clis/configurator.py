import re
from pathlib import Path
from typing import Literal

import click
from rich import box
from rich.console import Console
from rich.table import Table

from core.click_chore import YudoConfigs, ask, cmd, warning, AutoReadConfigPaser, curd


def get_frp_install_path() -> Path:
    """
    查找 frp 的安装目录。

    :raise KeyError: 配置不存在。
    :raise TypeError: 配置的是一个文件而非文件夹。
    :raise FileNotFoundError: 安装目录已设置，但不存在。
    """
    with YudoConfigs() as configs:
        path = Path(configs['frp']['path'])
        if not path.exists():
            raise FileNotFoundError
        if not path.is_dir():
            raise TypeError
        return path


def find_frp_configs(
        path: Path,
        scope: Literal['frpc', 'frps'],
) -> dict[str, tuple[Path, str, str]]:
    """
    查找 frp 的所有配置。

    :param path: frp 的安装目录。
    :param scope: 查找 frpc 还是 frps 的配置。
    :return: 以配置文件短名称为键，元组为值的字典。元组包含配置文件的路径、名称和后缀。
    """
    return {
        result.group(1): (fo.parent, fo.name, fo.suffix)
        for fo in path.iterdir()
        if (result := re.fullmatch(scope + r'_?(.*)\.ini', fo.name))
    }


def find_frp_config(
        path: Path,
        scope: Literal['frpc', 'frps'],
        name: str = None,
) -> Path:
    """
    通过短名称查找 frp 的某个配置文件。

    :param path: frp 的安装目录。
    :param scope: 前缀。指的是文件名中 {frpc}.ini 的括号部分。
    :param name: 短名称。指的是文件名中 frpc_{full}.ini 的括号部分，如果不提供则表示 frpc.ini。
    :return:
    :raise FileNotFoundError: 文件不存在。args[0] 是一个Path对象，表示文件地址。
    :raise TypeError: 目标不是一个文件。args[0] 是一个Path对象，表示文件地址。
    """
    cfp = path / (f'{scope}_{name}.ini' if name else f'{scope}.ini')
    if not cfp.exists():
        raise FileNotFoundError(cfp)
    if not cfp.is_file():
        raise TypeError(cfp)
    return cfp


def configurate_frp(instruction, pattern: str, filename: str, list_all: bool, delete_it: bool):
    try:
        path = get_frp_install_path()
    except (KeyError, FileNotFoundError):
        warning(
            '请先使用以下命令设置 frp 的安装目录：',
            cmd(configurate, 'conf', 'yudo', 'frp.path=YOUR_INSTALL_PATH'),
        )
        return
    except TypeError:
        warning(
            '请使用以下命令重新设置 frp 的安装目录：',
            cmd(configurate, 'conf', 'yudo', 'frp.path=YOUR_INSTALL_PATH'),
        )
        return

    if list_all:
        table = Table('简短名称', '查看方式', '文件名', box=box.SIMPLE_HEAD)
        for name, info in find_frp_configs(path, instruction.name).items():
            if name == '':
                command = cmd(configurate, instruction)
            else:
                command = cmd(configurate, instruction, '-c', name)
            table.add_row(name, command, info[1])
        else:
            console = Console()
            console.print(table)
    else:
        try:
            cfp = find_frp_config(path, instruction.name, filename)
        except TypeError as e:
            warning(f'这不是一个文件：{e.args[0]!s}')
            return
        except FileNotFoundError as e:
            cfp = e.args[0]
            warning(f'找不到配置文件：{cfp!s}')
            if not ask('创建它？(Y/[n]) '):
                return
            cfp.touch()

        parser = AutoReadConfigPaser(cfp)
        curd(parser, pattern, delete_it)


@click.group('conf', short_help='读取或写入配置文件')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def configurate():
    """
    读取或写入配置文件。
    """


@configurate.command('yudo', short_help='配置当前程序')
@click.argument('pattern', metavar='[SECTION[.KEY[=VALUE]]]', default='', required=False)
@click.option('-d', '--delete', 'delete_it', is_flag=True, help='删除某个配置项或整个配置节。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def configurate_yudo(pattern: str, delete_it: bool):
    curd(YudoConfigs(), pattern, delete_it)


@configurate.command('frpc', short_help='配置 frp 客户端')
@click.argument('pattern', metavar='[SECTION[.KEY[=VALUE]]]', default='', required=False)
@click.option('-l', '--list', 'list_all', is_flag=True, help='列举所有配置文件及相应的短名称。')
@click.option('-c', '--config', 'filename', default='', help='配置哪个文件。提供简短名称。')
@click.option('-d', '--delete', 'delete_it', is_flag=True, help='删除一个配置项或整个配置节。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def configurate_frpc(pattern: str, filename: str, list_all: bool, delete_it: bool):
    configurate_frp(configurate_frpc, pattern, filename, list_all, delete_it)


@configurate.command('frps', short_help='配置 frp 服务端')
@click.argument('pattern', metavar='[SECTION[.KEY[=VALUE]]]', default='', required=False)
@click.option('-l', '--list', 'list_all', is_flag=True, help='列举所有配置文件及相应的短名称。')
@click.option('-c', '--config', 'filename', default='', help='配置哪个文件。提供简短名称。')
@click.option('-d', '--delete', 'delete_it', is_flag=True, help='删除一个配置项或整个配置节。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def configurate_frps(pattern: str, filename: str, list_all: bool, delete_it: bool):
    configurate_frp(configurate_frps, pattern, filename, list_all, delete_it)
