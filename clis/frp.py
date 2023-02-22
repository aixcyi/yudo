import os
from typing import NoReturn, Literal

import click

from core.click_chore import AutoReadConfigPaser, cmd, ask, warning, curd
from core.style import *
from .configurator import configurate, get_frp_install_path, find_frp_config


def run_frp(
        prefix: Literal['frpc', 'frps'],
        filename: str,
        new_configs: tuple[str],
        print_it: bool,
) -> NoReturn:
    """
    运行 frpc 或 frps 程序。

    :param prefix: 配置文件名前缀。只能是“frpc”和“frps”。
    :param filename: 配置的简短名称。例如 “full” 代表 “frpc_full.ini”。
    :param new_configs: 多个符合表达式 [SECTION[.KEY[=VALUE]]] 的用户输入。
    :param print_it: 保存后打印当前配置。
    :return: 无。
    """
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
    try:
        cfp = find_frp_config(path, prefix, filename)
    except TypeError as e:
        warning(f'这不是一个文件：{e.args[0]!s}')
        return
    except FileNotFoundError as e:
        cfp = e.args[0]
        warning(f'找不到配置文件：{cfp!s}')
        if not ask('创建它？(Y/[n]) '):
            return
        cfp.touch()

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
            curd(configs, '', False)

    if prefix == 'frpc':
        os.execl(cfp.parent / 'frpc', 'http', '-c', str(cfp))
    elif prefix == 'frps':
        pass


@click.command('frpc', short_help='运行frp客户端')
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='用某个配置文件来运行。提供简短名称。使用 {} 列出所有。'.format(
                  cmd(configurate, "frpc", "--list")
              ))
@click.option('-s', '--set', 'new_configs', metavar='SECTION.KEY=VALUE',
              multiple=True, help='修改并保存配置后再运行。使用多个 -s 来修改多个配置。')
@click.option('-p', '-print', 'print_it', is_flag=True,
              help='运行前打印文件中的所有配置。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def run_frpc(filename: str | None, new_configs: tuple[str] | None, print_it: bool):
    """
    运行frp客户端（frpc）。
    """
    run_frp('frpc', filename, new_configs, print_it)


@click.command('frps', short_help='运行frp服务端')
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='用某个配置文件来运行。提供简短名称。使用 {} 列出所有。'.format(
                  cmd(configurate, "frps", "--list")
              ))
@click.option('-s', '--set', 'new_configs', metavar='SECTION.KEY=VALUE',
              multiple=True, help='修改并保存配置后再运行。使用多个 -s 来修改多个配置。')
@click.option('-p', '-print', 'print_it', is_flag=True,
              help='运行前打印文件中的所有配置。')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def run_frps(filename: str | None, new_configs: tuple[str] | None, print_it: bool):
    run_frp('frps', filename, new_configs, print_it)
