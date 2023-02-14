import click

from core.click_chore import YuConfiguration


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
        configs.curd(section, key, value)
