import click

from core.click_chore import YuConfiguration
from core.style import *


@click.command('conf', short_help='读取或覆写yudo的配置')
@click.argument('key', metavar='[SECTION[.KEY]]', default='', required=False)
@click.argument('value', required=False)
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def configurate(key: str | None, value: str | None):
    """
    读取或覆写yudo安装目录下的配置。一般用于yudo命令的自定义。
    """
    section, _, key = key.rpartition('.')
    if not section:
        section, key = key, ''

    with YuConfiguration() as configs:

        # 枚举所有节
        if not section:
            for _title, _section in configs.items():
                if _title == 'DEFAULT':
                    continue
                click.secho('[', fg=PT_CONF_SECTION, nl=False)
                click.secho(_title, nl=False)
                click.secho(']', fg=PT_CONF_SECTION)
                for _key in _section:
                    click.secho(_key, fg=PT_CONF_KEY, nl=False)
                    click.secho(' = ', fg=PT_CONF_EQU, nl=False)
                    click.secho(_section[_key])
                else:
                    click.secho()

        # 枚举一整节
        elif section and not key:
            if section not in configs:
                click.secho(f'找不到 {section} 。', err=True, fg=PT_WARNING)
                click.secho('注意：节名称是区分大小写的。', err=True, fg=PT_SPECIAL)
                return
            for k in configs[section]:
                click.secho(k, nl=False, fg=PT_CONF_KEY)
                click.secho('=', nl=False, fg=PT_CONF_EQU)
                click.secho(configs[section][k])

        # 打印某个配置项
        elif section and key and value is None:
            if section not in configs:
                click.secho(f'找不到 {section} 。', err=True, fg=PT_WARNING)
                return
            if key not in configs[section]:
                click.secho(f'找不到 {section} 下的 {key}。', err=True, fg=PT_WARNING)
                return
            click.secho(configs[section][key])

        # 设置配置值
        elif section and key and value is not None:
            configs.save_finally = True
            configs.ensure(section)[key] = value
