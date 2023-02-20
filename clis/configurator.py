import click

from core.click_chore import YudoConfigs
from core.style import *


@click.command('conf', short_help='读取或覆写yudo的配置')
@click.argument('pattern', metavar='[SECTION[.KEY[=VALUE]]]', default='', required=False)
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def configurate(pattern: str):
    """
    读取或覆写yudo安装目录下的配置。一般用于各个命令的自定义。
    """
    section, key, value = YudoConfigs.parse_path(pattern)

    with YudoConfigs() as configs:

        # 枚举所有节
        if not section:
            configs.print_all(nl=True)

        # 枚举一整节
        elif section and not key:
            if configs.check_section(section):
                configs.print_section(section)

        # 打印某个配置项
        elif section and key and value is None:
            if configs.check_key(section, key):
                click.secho(configs[section][key])

        # 设置配置值
        elif section and key and value:
            configs.ensure(section)[key] = value
            configs.save()


@click.command('disconf', short_help='删除yudo配置中的指定配置')
@click.argument('pattern', metavar='SECTION[.KEY]')
@click.help_option('-h', '--help', help='列出这份帮助信息。')
def remove_configuration(pattern: str):
    section, key, _ = YudoConfigs.parse_path(pattern)

    with YudoConfigs(auto_save=True) as configs:

        # 删除一个key
        if section and key:
            if not configs.check_key(section, key):
                return
            click.secho('是否确认删除？(Y/[n]) ', err=True, nl=False, fg=PT_WARNING)
            if input()[:1] != 'Y':
                return
            _ = configs[section].pop(key)

        # 删除整个section
        elif section and not key:
            if not configs.check_section(section):
                return
            click.secho('是否删除一整节？(Y/[n]) ', err=True, nl=False, fg=PT_WARNING)
            if input()[:1] != 'Y':
                return
            configs.remove_section(section)
