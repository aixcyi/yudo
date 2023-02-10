import click

from core.click_chore import YuConfiguration


@click.command('conf')
@click.argument('key', metavar='[SECTION[.KEY]]', default='', required=False)
@click.argument('value', required=False)
@click.help_option('-h', '--help')
def configurate(key: str | None, value: str | None):
    """
    读取或覆写yudo的配置。
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
                click.secho('[', fg='yellow', nl=False)
                click.secho(_title, nl=False)
                click.secho(']', fg='yellow')
                for _key in _section:
                    click.secho(_key, fg='cyan', nl=False)
                    click.secho(' = ', fg='yellow', nl=False)
                    click.secho(_section[_key])
                else:
                    click.secho()

        # 枚举一整节
        elif section and not key:
            if section not in configs:
                click.secho(f'找不到 {section} 。', err=True, fg='yellow')
                click.secho('注意：节名称是区分大小写的。', err=True, fg='magenta')
                return
            for k in configs[section]:
                click.secho(k, nl=False, fg='cyan')
                click.secho('=', nl=False, fg='yellow')
                click.secho(configs[section][k])

        # 打印某个配置项
        elif section and key and value is None:
            if section not in configs:
                click.secho(f'找不到 {section} 。', err=True, fg='yellow')
                return
            if key not in configs[section]:
                click.secho(f'找不到 {section} 下的 {key}。', err=True, fg='yellow')
                return
            click.secho(configs[section][key])

        # 设置配置值
        elif section and key and value is not None:
            configs.save_finally = True
            configs.ensure(section)[key] = value
