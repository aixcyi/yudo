import os
import re
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.table import Table

from core.click_chore import YudoConfigs, AutoReadConfigPaser
from core.style import *


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
            click.secho('未设置frp的安装目录。可以使用以下命令设置：\n'
                        'yu config frp.path YOUR_INSTALL_PATH',
                        err=True, fg=PT_WARNING)
            return None
        if not path.is_dir():
            click.secho('设置的不是一个目录。可以使用以下命令修改frp安装目录：\n'
                        'yu config frp.path YOUR_INSTALL_PATH',
                        err=True, fg=PT_WARNING)
            return None
        if not path.exists():
            click.secho('设置的frp安装目录不存在。可以使用以下命令重新设置：\n'
                        'yu config frp.path YOUR_INSTALL_PATH',
                        err=True, fg=PT_WARNING)
            return None

    # 在frp安装目录中拼接配置文件的地址
    # 并校验文件存在和属性
    cfp = path / (f'{prefix}_{short_name}.ini' if short_name else f'{prefix}.ini')
    if not cfp.exists():
        click.secho(f'配置文件 {cfp!s} 不存在。\n是否创建？(Y/[n]) ', err=True, nl=False, fg=PT_WARNING)
        if input()[:0] != 'Y':
            return None
        cfp.touch()
    if not cfp.is_file():
        click.secho(f'路径 {cfp!s} 不是一个文件。', err=True, fg=PT_WARNING)
        return None

    return cfp


@click.group('frpc', short_help='管理、配置、运行frp客户端（frpc）')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def manage_frpc():
    """
    管理、配置、运行frp客户端（frpc）。

    使用前要先配置frp的安装目录，命令是 yu conf frp.path YOUR_PATH。
    """


@manage_frpc.command('list', short_help='列出frpc所有配置')
def frpc_list_configs():
    if not (cfp := get_cfp()):
        return

    table = Table('简短名称', '文件名称', '查看方式', box=box.SIMPLE_HEAD)
    for d in cfp.parent.iterdir():
        result = re.fullmatch(r'frpc_?(.*)\.ini', d.name)
        if not result:
            continue
        name = result.group(1)
        command = f'yu frpc get -c {name}' if name else 'yu frpc get'
        table.add_row(name, d.name, command)
    else:
        console = Console()
        console.print(table)


@manage_frpc.command('set', short_help='查看或修改frpc的配置')
@click.argument('key', metavar='SECTION[.KEY', default='', required=False)
@click.argument('value', metavar='NEW_VALUE', required=False)
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='要修改哪个配置文件，提供简短名称即可。比如 frpc_full.ini 的简短名称就是 full')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def frpc_set_configs(
        key: str, value: str | None, filename: str | None,
):
    """
    设置一个配置项，或者查看配置项。

    例如：
      - 打印文件："yu frpc set"
      - 打印某节："yu frpc set common"
      - 打印配置："yu frpc set common.server_port"
      - 修改配置："yu frpc set common.server_port 65535"

    默认围绕 frpc.ini 进行操作，假设要对  frpc_full.ini 操作，就需要附加 -c full 选项。
    """
    if not (cfp := get_cfp(filename)):
        return
    section, _, key = key.rpartition('.')
    if not section:
        section, key = key, ''

    with AutoReadConfigPaser(cfp, auto_patch=True) as configs:
        # 打印整个配置文件
        if not section:
            configs.print_all(nl=True)
            return

        if section not in configs:
            click.secho(f'找不到 {section} 。', err=True, fg=PT_WARNING)
            click.secho('注意：节名称是区分大小写的。', err=True, fg=PT_SPECIAL)
            return

        # 打印一整个section
        if not key:
            configs.print_section(section)
            return

        if key not in configs[section]:
            click.secho(f'在 {section} 中找不到 {key} 。', err=True, fg=PT_WARNING)
            click.secho('注意：名称是区分大小写的。', err=True, fg=PT_SPECIAL)
            return

        # 打印具体配置
        if not value:
            click.secho(configs[section][key])
            return

        configs[section][key] = value
        configs.save()


@manage_frpc.command('run', short_help='运行frp客户端')
@click.option('-c', '--config', 'filename', metavar='NAME',
              help='用某个配置文件来运行。提供简短名称。使用 yu frpc conf -l 查看所有。')
@click.option('-s', '--set', 'new_configs', metavar='SECTION.KEY VALUE',
              multiple=True, nargs=2, help='修改并保存配置后再运行。')
@click.option('-p', '-print', 'print_it', is_flag=True,
              help='运行前打印文件中的所有配置。')
def run_frpc(
        filename: str | None,
        new_configs: tuple[tuple[str, str]] | None,
        print_it: bool,
):
    if not (cfp := get_cfp(filename)):
        return

    if new_configs:
        with AutoReadConfigPaser(cfp, auto_patch=True) as configs:
            for c in new_configs:
                snk, value = c
                section, _, key = snk.rpartition('.')
                if not all([section, key, value]):
                    click.secho(f'配置格式无法解析。', err=True, fg=PT_WARNING)
                    return None
                configs[section][key] = value
                configs.save()

    if print_it:
        with AutoReadConfigPaser(cfp, auto_patch=True) as configs:
            configs.print_all()

    os.execl(cfp.parent / 'frpc', 'http', '-c', str(cfp))
