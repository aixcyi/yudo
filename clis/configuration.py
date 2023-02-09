import click

from core.click_chore import YuConfiguration


@click.command('conf')
@click.argument('key', metavar='SECTION[.KEY]')
@click.argument('value', default=None, required=False)
@click.help_option('-h', '--help')
def configurate(key: str, value: str | None):
    """
    读取或写入配置项。
    """
    with YuConfiguration() as configs:
        section, _, key = key.rpartition('.')
        if not section:
            if not key:
                return
            section, key = key, ''
        if section not in configs:
            configs[section] = {}

        if not key:
            if value:
                click.secho('<Section不能设置默认值>', err=True, fg='yellow')
                return
            for k in configs[section]:
                click.secho(f'{k}={configs[section][k]}')
            return
        if not value:
            click.secho(configs[section][key])
            return

        section = configs[section]
        section[key] = value
        configs.save_now()
